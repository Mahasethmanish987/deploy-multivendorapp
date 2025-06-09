import base64
import hashlib
import hmac
import json
import os
import uuid

from accounts.utils import send_notification
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from marketplace.models import Cart
from menu.models import FoodItem
from vendor.models import Vendor
from xhtml2pdf import pisa

from .forms import OrderForm
from .models import CustomerRefund, Order, OrderedFood, Payment
from .utils import generate_order


@login_required(login_url="accounts:login")
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect("marketplace:marketplace")
    vendor_ids = []
    vendor_opening_ids = set()
    k = {}

    for cart_item in cart_items:
        if cart_item.fooditem.vendor.id not in vendor_ids:
            vendor_ids.append(cart_item.fooditem.vendor.id)

    total_data = {}
    grand_total = 0
    for cart_item in cart_items:
        fooditem = FoodItem.objects.select_related("vendor").get(
            id=cart_item.fooditem.id, vendor__in=vendor_ids
        )
        if fooditem.vendor.is_open():
            v_id = fooditem.vendor.id
            vendor_opening_ids.add(v_id)

            if v_id in k:
                total = k[v_id]
                total += fooditem.price * cart_item.quantity
                k[v_id] = total
                grand_total=total
                

            else:
                total = fooditem.price * cart_item.quantity
                k[v_id] = total
                grand_total += total
            total_data.update({fooditem.vendor.id: str(total)})

    for item in cart_items:
        item.vendor_is_open = item.fooditem.vendor.id in vendor_opening_ids
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data["first_name"]
            order.last_name = form.cleaned_data["last_name"]
            order.phone = form.cleaned_data["phone"]
            order.email = form.cleaned_data["email"]
            order.address = form.cleaned_data["address"]
            order.country = form.cleaned_data["country"]
            order.state = form.cleaned_data["state"]
            order.pin_code = form.cleaned_data["pin_code"]
            order.user = request.user
            order.total = grand_total
            order.total_data = json.dumps(total_data)
            order.payment_method = request.POST["payment_method"]
            order.save()
            order.order_number = generate_order(request.user, order.id)
            vendor_instances = Vendor.objects.filter(id__in=vendor_opening_ids)
            order.vendors.add(*vendor_instances)
            order.save()
            context = {
                "order": order,
                "cart_items": cart_items,
                "grand_total": grand_total,
            }

            if order.payment_method == "esewa":
                request.session["order_id"] = order.order_number
                context["api_url"] = "https://foodonline.run.place/order/esewacredentials/"
                return render(request, "order/place_order.html", context)
            else:
                return render(request, "marketplace/checkout.html", {"form": form})

    else:
        return redirect("marketplace:checkout")


def esewacredentials(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "please login"})
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "Failed", "message": "Invalid request"})
    secret_key = "8gBm/:&EnhH.1/q"
    transaction_uuid = uuid.uuid4()
    product_code = "EPAYTEST"
    order = Order.objects.get(order_number=request.session.get("order_id"))
    amount = order.total
    message = f"total_amount={amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    hash = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    has_in_base64 = base64.b64encode(hash).decode()

    return JsonResponse(
        {
            "status": "success",
            "message": "the data are below",
            "transaction_uuid": transaction_uuid,
            "product_code": product_code,
            "amount": amount,
            "signature": has_in_base64,
        }
    )


def failed_handle_esewa(request):
    order_number = request.session.get("order_id")
    order = Order.objects.get(user=request.user, order_number=order_number)
    cart_items = Cart.objects.select_related("fooditem__vendor").filter(
        user=request.user
    )
    del request.session["order_id"]
    order.status = "cancelled"
    order.is_ordered = False
    order.save()
    for item in cart_items:
        vendor = item.fooditem.vendor
        if vendor.is_open():
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.user = request.user

            ordered_food.fooditem = item.fooditem
            ordered_food.quantity = item.quantity
            ordered_food.price = item.fooditem.price
            ordered_food.amount = item.fooditem.price * item.quantity
            ordered_food.status = "cancelled_in_payment_gateway"
            ordered_food.save()
    return redirect("order:order_list")


def handle_esewa(request):
    encoded_string = request.GET.get("data")
    decoded_bytes = base64.b64decode(encoded_string)
    decoded_string = decoded_bytes.decode("utf-8")
    decoded_json = json.loads(decoded_string)
    transaction_id = decoded_json.get("transaction_code")
    order_number = request.session.get("order_id")

    if Payment.objects.filter(transaction_id=transaction_id).exists():
        del request.session["order_id"]
        return redirect(
            f"/order/order_complete/?order_no={order_number}&trans_id={transaction_id}"
        )

    status = decoded_json.get("status")
    order = Order.objects.get(user=request.user, order_number=order_number)
    payment = Payment(
        user=request.user,
        transaction_id=transaction_id,
        amount=order.total,
        status="complete",
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.status = "completed"
    order.save()

    to_emails = set()
    cart_items = Cart.objects.select_related("fooditem__vendor").filter(
        user=request.user
    )
    for item in cart_items:
        vendor = item.fooditem.vendor
        if vendor.is_open():
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.user = request.user
            ordered_food.payment = payment
            ordered_food.fooditem = item.fooditem
            ordered_food.quantity = item.quantity
            ordered_food.price = item.fooditem.price
            ordered_food.amount = item.fooditem.price * item.quantity
            ordered_food.status = "pending"
            ordered_food.save()
            to_emails.add(item.fooditem.vendor.user.email)
            item.delete()

    mail_subject = "Thanks for ordering with us"
    mail_template = "order/order_confirmation_email.html"
    context = {
        "user_first_name": order.first_name,
        "order_id": order.order_number,
        "order_transaction_id": order.payment.transaction_id,
        "to_email": order.email,
    }

    send_notification.delay(mail_subject, mail_template, context)
    mail_subject = "You have received an  order"
    mail_template = "order/new_order_received.html"
    context = {"to_email": list(to_emails)}
    send_notification.delay(mail_subject, mail_template, context)
    order_complete_url = "/order/order_complete/"
    redirect_url = (
        f"{order_complete_url}?order_no={order_number}&trans_id={transaction_id}"
    )
    return redirect(redirect_url)


def order_complete(request):
    order_number = request.GET.get("order_no")
    transaction_id = request.GET.get("trans_id")

    try:
        order = Order.objects.get(order_number=order_number)
        ordered_food = OrderedFood.objects.filter(order=order)
        subtotal = 0

        for item in ordered_food:
            subtotal += item.amount
        context = {
            "order": order,
            "ordered_food": ordered_food,
            "subtotal": subtotal,
        }
        return render(request, "order/order_complete.html", context)
    except Order.DoesNotExist:
        print(
            f"order with number{order_number} and transaction ID {transaction_id} not found"
        )
        return redirect("myapp:index")
    except Exception as e:
        print(f"unexpecteed error:{e}")
        return redirect("myapp:index")


@login_required(login_url="accounts:login")
def update_order_status(request):
    if request.method == "POST":
        ordered_id = request.POST.get("food_id")
        new_status = request.POST.get("status")

        try:
            ordered_food = OrderedFood.objects.get(id=ordered_id)

        except OrderedFood.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid item"})

        ordered_food.status = new_status
        if ordered_food.status == "completed":
            pass
        ordered_food.save()
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"order_{ordered_food.id}",
            {"type": "order_update", "food_id": ordered_food.id, "status": new_status},
        )
        # return JsonResponse({"success": True, "message": "Invalid item"})


def download_pdf(request, order_number):
    order = Order.objects.get(order_number=order_number)
    base_url = request.build_absolute_uri("/")[:-1]
    html = render_to_string(
        "order/pdf_template.html",
        {
            "order": order,
            "ordered_food": order.orders.all(),
            "base_url": "http://foodonline.run.place",
            "subtotal": order.total,
        },
    )
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=order_{order_number}.pdf"

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback,  # Handle static files
    )
    if pisa_status.err:
        return HttpResponse("PDF generation error!")
    return response


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths for xhtml2pdf
    """
    """Convert HTML URIs to absolute system paths"""
    try:
        # Static files
        if uri.startswith(settings.STATIC_URL):
            path = os.path.join(
                str(settings.STATIC_ROOT),  # ← Explicit string conversion
                uri.replace(settings.STATIC_URL, "", 1),
            )
        # Media files
        elif uri.startswith(settings.MEDIA_URL):
            path = os.path.join(
                str(settings.MEDIA_ROOT),  # ← Explicit string conversion
                uri.replace(settings.MEDIA_URL, "", 1),
            )
        else:
            return uri  # Return unchanged

        # Validate path
        if not os.path.isfile(path):
            raise Exception(f"File not found: {path}")

        return path

    except Exception as e:
        print(f"Error processing URI {uri}: {str(e)}")
        return uri


@login_required(login_url="accounts:login")
def order_list(request):
    orders = (
        Order.objects.filter(user=request.user)
        .exclude(status="new")
        .order_by("-created_at")
        .prefetch_related("orders")
    )
    context = {"orders": orders}

    return render(request, "order/order_list.html", context)


@login_required(login_url="accounts:login")
def order_detail(request, order_number):
    ordered_foods = OrderedFood.objects.filter(
        order__order_number=order_number
    ).select_related("order", "fooditem")
    context = {"ordered_foods": ordered_foods}
    return render(request, "order/order_detail.html", context)


@login_required(login_url="accounts:login")
def vendor_order_list(request):
    vendor = Vendor.objects.get(user=request.user)
    orders = (
        Order.objects.filter(vendors=vendor)
        .order_by("-created_at")
        .exclude(status="new")
        .prefetch_related(
            Prefetch(
                "orders", queryset=OrderedFood.objects.filter(fooditem__vendor=vendor)
            )
        )
    )
    
    for order in orders:
        total = 0
        for item in order.orders.all():
            total += item.amount
        order.total1=total 
    return render(
        request, "order/vendor_order_list.html", {"orders": orders}
    )


@login_required(login_url="accounts:login")
def vendor_order_detail(request, order_number):
    vendor = Vendor.objects.get(user=request.user)

    ordered_foods = OrderedFood.objects.filter(
        order__order_number=order_number, fooditem__vendor=vendor
    ).select_related("order", "fooditem")
    context = {"ordered_foods": ordered_foods}
    return render(request, "order/vendor_order_detail.html", context)

@login_required(login_url='accounts:login')
def earnings_report(request):
    # Get all time periods
    user=request.user 
    vendor=Vendor.objects.get(user=user)
    context = {
        "today": OrderedFood.todays_earnings(vendor),
        "weekly": OrderedFood.weekly_earnings(vendor),
        "monthly": OrderedFood.monthly_earnings(vendor),
        "total": OrderedFood.total_earnings(vendor),
        "monthly_breakdown": OrderedFood.all_months_earnings(vendor),
        "current_date": timezone.localtime(timezone.now()).strftime("%Y-%m-%d"),
    }
    return render(request, "order/earnings_report.html", context)


@csrf_exempt
def server_update_order_status(request):
    
    
    if request.method == "POST":
        ordered_id = request.POST.get("food_id")
        new_status = request.POST.get("status")

        try:
            ordered_food = OrderedFood.objects.get(id=ordered_id)

        except OrderedFood.DoesNotExist:
            return JsonResponse({"success": False, "message": "Invalid item"})

        ordered_food.status = new_status
        if ordered_food.status == "completed":
            pass
        ordered_food.save()
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"order_{ordered_food.id}",
            {"type": "order_update", "food_id": ordered_food.id, "status": new_status},
        )
        return JsonResponse({"success": True, "message": "Invalid item"})


def refunds(request):
    refunds = CustomerRefund.objects.filter(customer=request.user).order_by(
        "-created_at"
    )
    context = {"refunds": refunds}
    return render(request, "order/refunds.html", context)


def refund_detail(request, pk):
    refunds = CustomerRefund.objects.get(pk=pk)

    context = {"refunds": refunds}
    return render(request, "order/refund_detail.html", context)

from .models import VendorPayout
def vendor_payout(request):
    vendor=Vendor.objects.get(user=request.user)
    payouts=VendorPayout.objects.filter(vendor=vendor).order_by('-created_at')
    context={
        'payouts':payouts
    }
    return render(request,'order/vendor_payout.html',context)

def vendor_payout_detail(request,pk):
    vendor=Vendor.objects.get(user=request.user)
    payouts=VendorPayout.objects.get(vendor=vendor,pk=pk)
    context={
        'payouts':payouts
    }
    return render(request,'order/vendor_payout_detail.html',context)