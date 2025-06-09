import base64
import hashlib
import hmac
import json
import uuid

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from order.models import CustomerRefund, Payment, VendorPayout
from accounts.utils import send_notification
# Create your views here.


def admin_check(user):
    return user.is_authenticated and user.is_admin


@user_passes_test(admin_check)
def adminDashboard(request):
    print("admin dashboard view called")
    pending_payouts = VendorPayout.objects.filter(status="pending").count()
    pending_refunds = CustomerRefund.objects.filter(status="pending").count()

    context = {"pending_payouts": pending_payouts, "pending_refunds": pending_refunds}
    return render(request, "admin/dashboard.html", context)


@user_passes_test(admin_check)
def custAdminDashboard(request):
    pending_refunds = CustomerRefund.objects.filter(
        status__in=["pending", "failed"], is_fully_cancelled=True
    )
    return render(
        request, "admin/refund_list1.html", {"pending_refunds": pending_refunds}
    )


@user_passes_test(admin_check)
def vendorAdminDashboard(request):
    pass


@require_POST
def process_esewa(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "please login"})
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "Failed", "message": "Invalid request"})

    refund_id = request.POST.get("refund_id")
    refund_amount = request.POST.get("refund_amount")
    previous_refund_id = request.session.get("refund_id")
    if previous_refund_id != refund_id:
        request.session["refund_id"] = refund_id
    secret_key = "8gBm/:&EnhH.1/q"
    transaction_uuid = uuid.uuid4()
    product_code = "EPAYTEST"

    message = f"total_amount={refund_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    hash = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    has_in_base64 = base64.b64encode(hash).decode()
    return JsonResponse(
        {
            "status": "success",
            "message": "the data are below",
            "transaction_uuid": transaction_uuid,
            "product_code": product_code,
            "amount": refund_amount,
            "signature": has_in_base64,
        }
    )


def success_handle_esewa(request):
    encoded_string = request.GET.get("data")
    decoded_bytes = base64.b64decode(encoded_string)
    decoded_string = decoded_bytes.decode("utf-8")
    decoded_json = json.loads(decoded_string)
    transaction_id = decoded_json.get("transaction_code")
    status = decoded_json.get("status")
    refund_id = request.session.get("refund_id")

    refund = CustomerRefund.objects.get(id=refund_id)
    payment = Payment.objects.create(
        user=refund.customer,
        transaction_id=transaction_id,
        amount=refund.refund_amount,
        status="complete",
    )
    refund.payment = payment
    refund.status = "completed"
    refund.save()

    return redirect("admins:refund_list")


def failure_handle_esewa(request):
    refund_id = request.session.get("refund_id")
    refund = CustomerRefund.objects.get(id=refund_id)
    refund.status = "failed"
    refund.save()
    return redirect("admins:refund_list")


def payout_list(request):
    payouts = VendorPayout.objects.filter(status__in=["pending", "cancelled"])
    print(payouts)
    context = {"payouts": payouts}
    return render(request, "admin/vendor_list.html", context)


@require_POST
def vendor_process_esewa(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "please login"})
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "Failed", "message": "Invalid request"})

    payout_id = request.POST.get("payout_id")
    payout_amount = request.POST.get("payout_amount")
    previous_payout_id = request.session.get("payout_id")
    if previous_payout_id != payout_id:
        request.session["payout_id"] = payout_id
    secret_key = "8gBm/:&EnhH.1/q"
    transaction_uuid = uuid.uuid4()
    product_code = "EPAYTEST"
    print(payout_amount, transaction_uuid, product_code)

    message = f"total_amount={payout_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    hash = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    has_in_base64 = base64.b64encode(hash).decode()
    
    return JsonResponse(
        {
            "status": "success",
            "message": "the data are below",
            "transaction_uuid": transaction_uuid,
            "product_code": product_code,
            "amount": payout_amount,
            "signature": has_in_base64,
        }
    )


def vendor_success_handle_esewa(request):
    encoded_string = request.GET.get("data")
    decoded_bytes = base64.b64decode(encoded_string)
    decoded_string = decoded_bytes.decode("utf-8")
    decoded_json = json.loads(decoded_string)
    transaction_id = decoded_json.get("transaction_code")
    status = decoded_json.get("status")
    payout_id = request.session.get("payout_id")

    payout = (
        VendorPayout.objects.select_related("vendor","vendor__user").get(id=payout_id)
        
        
    )
    payment = Payment.objects.create(
        user=payout.vendor.user,
        transaction_id=transaction_id,
        amount=payout.net_amount,
        status="complete",
    )
   
    payout.payout_date = timezone.now()
    payout.payment = payment
    payout.status = "completed"
    payout.save()
    mail_template = "admin/payout_email_receipt.html"
    mail_subject = "payment details"
    context = {
        'vendor_name':payout.vendor.vendor_name,
        'amount':payout.net_amount,
        'transaction_id':transaction_id,
        'transaction_date':timezone.localtime(payout.payout_date).strftime('%Y-%m-%d %H:%M:%S'),
        'to_email':payout.vendor.user.email,
        'payout_id':payout.id
        
    }
    send_notification.delay(mail_subject,mail_template,context)
    

    return redirect("admins:payout_list")


def vendor_failure_handle_esewa(request):
    payout_id = request.session.get("payout_id")
    payout = VendorPayout.objects.get(id=payout_id)
    payout.status = "cancelled"
    utc_now = timezone.now()
    
    payout_date = utc_now
    payout.payout_date = payout_date
    payout.save()
    return redirect("admins:payout_list")
