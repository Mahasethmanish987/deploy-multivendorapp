import logging

from django.db import DatabaseError

from .models import Cart

logger = logging.getLogger(__name__)


def get_cart_counter(request):
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items:
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
            else:
                cart_count = 0
        except:
            cart_count = 0

    return {"cart_count": cart_count}


def cart_amount(request):
    cart_amount = 0
    print('hlwworld')
    if request.user.is_authenticated:
        try:
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items:
                for cart_item in cart_items:
                    cart_amount += cart_item.quantity * cart_item.fooditem.price
            
        except DatabaseError:
            # Log database errors
            logger.error("Database error")
            cart_amount=0
        except Exception as e:
            
            # Catch any other unexpected errors
            logger.critical(f"Unexpected error : {str(e)}")
            cart_amount=0

       

    
    return {"cart_amount": cart_amount}
