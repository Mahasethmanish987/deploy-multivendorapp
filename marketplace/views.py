import logging
import re
from order.forms import OrderForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import DatabaseError
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django_ratelimit.decorators import ratelimit
from menu.models import Category, FoodItem
from vendor.models import Vendor

from .context_processor import cart_amount, get_cart_counter
from .models import Cart

logger = logging.getLogger(__name__)


# Create your views here.
@ratelimit(key="ip", rate="10/m")
def marketplace(request):
    try:
        vendors = Vendor.objects.filter(
            user__is_active=True, is_approved=True
        ).select_related("user")
        vendor_count = vendors.count()
        paginator = Paginator(vendors, 2)
        page_number = request.GET.get("page")

        try:
            page_obj = paginator.get_page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)
        context = {"vendors": page_obj, "vendor_count": vendor_count}
        return render(request, "marketplace/marketplace.html", context)

    except DatabaseError as e:
        # Log database errors
        logger.error(f"Database error in vendor list: {str(e)}")

        messages.error(
            request, "We're having technical difficulties. Please try later."
        )
        return redirect("myapp:index")

    except Exception as e:
        # Catch any other unexpected errors
        logger.critical(f"Unexpected error in vendor list: {str(e)}")

        messages.error(request, "Something went wrong. Our team has been notified.")
        return redirect("myapp:index")


@ratelimit(key="ip", rate="10/m")
def vendor_detail(request, vendor_slug):
    try:
        vendor_instance = get_object_or_404(Vendor, vendor_slug=vendor_slug)
        categories = Category.objects.filter(vendor=vendor_instance).prefetch_related(
            Prefetch(
                "fooditem_set", queryset=FoodItem.objects.filter(is_available=True)
            )
        )
        cart_items = None
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)

        context = {
            "Vendor": vendor_instance,
            "categories": categories,
            "cart_items": cart_items,
        }

        return render(request, "marketplace/vendor_detail.html", context)
    except DatabaseError as e:
        # Log database errors
        logger.error(f"Database error in vendor list: {str(e)}")

        messages.error(
            request, "We're having technical difficulties. Please try later."
        )
        return redirect("marketplace:marketplace")

    except Exception as e:
        # Catch any other unexpected errors
        logger.critical(f"Unexpected error in vendor list: {str(e)}")

        messages.error(request, "Something went wrong. Our team has been notified.")
        return redirect("marketplace:marketplace")


def increase_cart(request, slug):
    # 1. Basic validation and request checks
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "Please login"})

    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse(
            {"status": "failed", "message": "Invalid request type"}, status=400
        )

    if not re.match(r"^[\w-]+$", slug):
        return JsonResponse({"status": "failed", "message": "Invalid product ID"})

    # 2. Business logic
    try:
        fooditem = FoodItem.objects.get(food_slug=slug)
    except FoodItem.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Food item not found"})
    except DatabaseError as e:
        logger.error(f"[DB ERROR] While fetching FoodItem (slug={slug}): {e}")
        return JsonResponse(
            {"status": "error", "message": "Database error"}, status=500
        )

    try:
        cart_item, created = Cart.objects.get_or_create(
            user=request.user, fooditem=fooditem, defaults={"quantity": 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            message = "Cart item quantity increased"
        else:
            message = "Cart item created"

        # 3. Response
        response_data = {
            "status": "success",
            "message": message,
            "quantity": cart_item.quantity,
            "get_cart_count": get_cart_counter(request),
            "cart_amount": cart_amount(request),
        }
        return JsonResponse(response_data)

    except DatabaseError as e:
        logger.error(
            f"[DB ERROR] While updating/creating Cart (user={request.user.id}): {e}"
        )
        return JsonResponse({"status": "error", "message": "Database error"})

    except Exception as e:
        logger.critical(f"[UNEXPECTED ERROR] in increase_cart: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": "An unexpected error occurred"}
        )


def decrease_cart(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "Please login"})

    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "failed", "message": "Invalid request type"})

    if not re.match(r"^[\w-]+$", slug):
        return JsonResponse({"status": "failed", "message": "Invalid product ID"})

    # 2. Business logic
    try:
        fooditem = FoodItem.objects.get(food_slug=slug)
    except FoodItem.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Food item not found"})
    except DatabaseError as e:
        logger.error(f"[DB ERROR] While fetching FoodItem (slug={slug}): {e}")
        return JsonResponse({"status": "error", "message": "Database error"})
    try:
        cart_items = Cart.objects.get(fooditem=fooditem, user=request.user)
        if cart_items.quantity <= 1:
            cart_items.quantity = 0
            cart_items.delete()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "cart_item deleted",
                    "quantity": 0,
                    "get_cart_count": get_cart_counter(request),
                    "cart_amount": cart_amount(request),
                }
            )
        cart_items.quantity -= 1
        cart_items.save()
        return JsonResponse(
            {
                "status": "success",
                "message": "cart_item decreased",
                "quantity": cart_items.quantity,
                "get_cart_count": get_cart_counter(request),
                "cart_amount": cart_amount(request),
            }
        )
    except Cart.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Item not found in cart"})
    except DatabaseError as e:
        logger.error(
            f"[DB ERROR] While updating/creating Cart (user={request.user.id}): {e}"
        )
        return JsonResponse({"status": "error", "message": "Database error"})

    except Exception as e:
        logger.critical(f"[UNEXPECTED ERROR] in increase_cart: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": "An unexpected error occurred"}
        )


def delete_cart(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required", "message": "Please login"})

    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "failed", "message": "Invalid request type"})

    # 2. Business logic

    try:
        cart_item = Cart.objects.get(user=request.user, id=id)
        cart_item.delete()
        return JsonResponse(
            {
                "status": "success",
                "message": "Item removed from cart",
                "get_cart_count": get_cart_counter(request),
                "cart_amount": cart_amount(request),
            }
        )
    except Cart.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Item not found in cart"})
    except DatabaseError as e:
        logger.error(
            f"[DB ERROR] While updating/creating Cart (user={request.user.id}): {e}"
        )
        return JsonResponse({"status": "error", "message": "Database error"})

    except Exception as e:
        logger.critical(f"[UNEXPECTED ERROR] in increase_cart: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": "An unexpected error occurred"}
        )


@login_required(login_url="accounts:login")
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    context = {"cart_items": cart_items}
    return render(request, "marketplace/cart.html", context)


def search(request):
    if request.method == "GET":
        address = request.GET.get("address")
        rest_name = request.GET.get("rest_name")
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius")

        fetch_vendor_by_fooditems = FoodItem.objects.filter(
            food_title__icontains=rest_name, is_available=True
        ).values_list("vendor", flat=True)
        vendors = Vendor.objects.filter(
            Q(id__in=fetch_vendor_by_fooditems) | Q(vendor_name__icontains=rest_name)
        )

        if lat and lng and radius:
            print("hlw world")
            pnt = GEOSGeometry("POINT(%s %s)" % (lng, lat))
            vendors = (
                Vendor.objects.filter(
                    Q(id__in=fetch_vendor_by_fooditems)
                    | Q(
                        vendor_name__icontains=rest_name,
                        is_approved=True,
                        user__is_active=True,
                    ),
                    user_profile__location__distance_lte=(pnt, D(km=radius)),
                )
                .annotate(distance=Distance("user_profile__location", pnt))
                .order_by("distance")
            )

            for v in vendors:
                v.kms = round(v.distance.km, 1)

        vendor_count = vendors.count()
        paginator = Paginator(vendors, 1)
        page_number = request.GET.get("page")

        try:
            page_obj = paginator.get_page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)
        params = request.GET.copy()
        params.pop("page", None)
        context = {
            "vendors": page_obj,
            "vendor_count": vendor_count,
            "source_location": address,
            "params": request.GET.urlencode(),
        }
        return render(request, "marketplace/search_list.html", context)


@login_required(login_url="accounts:login")
def check_vendor_status(request):
    cart_items = Cart.objects.filter(user=request.user)
    closed_vendors = set()
    opened_vendors = set()

    for item in cart_items:
        vendor = item.fooditem.vendor
        if not vendor.is_open():
            closed_vendors.add(vendor.vendor_name)
        else:
            opened_vendors.add(vendor.vendor_name)

    print(closed_vendors, opened_vendors)
    return JsonResponse(
        {"closed_vendors": list(closed_vendors), "opened_vendors": list(opened_vendors)}
    )


@login_required(login_url="accounts:login")
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by("created_at")
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect("marketplace:marketplace")

    default = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "phone": request.user.phone_number,
    }
    form=OrderForm(initial=default)
    context={
        'form':form,
        'cart_items':cart_items
    }
    return render(request,'marketplace/checkout.html',context)