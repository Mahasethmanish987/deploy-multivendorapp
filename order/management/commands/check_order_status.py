from django.core.management.base import BaseCommand
from order.models import OrderedFood
from datetime import timedelta
from accounts.utils import send_notification
import requests

class Command(BaseCommand):
    help = "Check order status and send notification/cancellations"

    def handle(self, *args, **kwargs):
        # Get active orders not complteed/cancelled
        
        active_orders = OrderedFood.objects.exclude(
            status__in=["completed", "cancelled"]
        )

        for order in active_orders: 
            if order.is_expired():
                response=requests.post("https://172.31.47.230:8000/order/server-update-order-status",data={'food_id':order.id,'status':'cancelled'})            
                
                continue 
            
            elapsed=order.time_since_creation()
            total_allowed = timedelta(minutes=4)
            remaining = total_allowed - elapsed
            
            # Convert remaining time to hours and minutes
            remaining_hours = remaining.seconds // 3600
            remaining_minutes = (remaining.seconds // 60) % 60
            
            if timedelta(minutes=3) <=elapsed <= timedelta(minutes=4):
                mail_template='order/order_warning.html'
                mail_subject='You have only one hour left for crossing the border'
                context={
                    'to_email':order.fooditem.vendor.user.email,
                    'order':order,
                    'total_remaining': f"{remaining_hours}h {remaining_minutes}m"
                }
                send_notification(mail_subject,mail_template,context)
                print('warning time')
            elif timedelta(minutes=2)<=elapsed <timedelta(minutes=3):
                mail_template='order/order_warning.html'
                mail_subject='only 2 hour left for crossing the order'
                context={
                    'to_email':order.fooditem.vendor.user.email,
                    'order':order,
                    'total_remaining': f"{remaining_hours}h {remaining_minutes}m"
                }
                send_notification(mail_subject,mail_template,context)
                print('warning time 1 ')

            
