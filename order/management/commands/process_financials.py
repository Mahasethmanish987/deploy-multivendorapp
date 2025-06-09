from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time as datetime_time
from django.db import transaction
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from order.models import Order,OrderedFood,VendorPayout,Payment
from vendor.models import Vendor 
from django.db.models import Sum, DecimalField
from decimal import Decimal

class Command(BaseCommand):
    help = "Process daily vendor payouts and customer refunds (Asia/Kathmandu Time)"
    
    def handle(self, *args, **options):
        self.process_vendor_payouts()
       
    
    def process_vendor_payouts(self):
        """Process daily vendor payouts with Kathmandu timezone logic"""
        try:
            # Kathmandu time parameters
            now_npt = timezone.localtime()
            
            grace_hours = 3  # Until 3 AM next day
            commission_rate = Decimal('0.15')

            # Calculate time window
            cutoff_date = (now_npt - timedelta(days=1)).date()
            print(cutoff_date)
            start_time = timezone.make_aware(datetime.combine(cutoff_date, datetime_time.min))
            end_time = start_time + timedelta(hours=24 + grace_hours)
            print(start_time)
            print(end_time)
            print(timezone.now())

            vendors = Vendor.objects.filter(is_approved=True)
            
            for vendor in vendors:
                with transaction.atomic():
                    # Get completed food items within time window
                    completed_items = OrderedFood.objects.filter(
                        fooditem__vendor=vendor,
                        status='completed',
                        # updated_at__range=(start_time, end_time),
                        is_payout_processed=False
                    ).select_related('order', 'fooditem', 'order__user')

                    if not completed_items.exists():
                        continue

                    # Calculate totals
                    aggregation = completed_items.aggregate(
                        total_amount=Sum('amount'),
                        item_count=Sum('quantity')
                    )
                    total_amount = aggregation['total_amount'] or 0
                    commission = total_amount * commission_rate
                    net_amount = total_amount - commission

                    # Build JSON snapshots with NPT timestamps
                    order_data = {}
                    food_data = []
                    
                    for item in completed_items:
                        # Convert to Kathmandu time
                        created_npt = timezone.localtime(item.created_at)
                        completed_npt = timezone.localtime(item.updated_at)

                        # Skip items created outside cutoff date
                        # if created_npt.date() != cutoff_date:
                        #     continue

                        # Food item snapshot
                        food_data.append({
                            'id': item.id,
                            'food_title': item.fooditem.food_title,
                            'price': str(item.price),
                            'quantity': item.quantity,
                            'amount':str(item.amount),
                            'ordered_at': created_npt.isoformat(),
                            'completed_at': completed_npt.isoformat()
                        })

                        # Order snapshot
                        order = item.order
                        if order.id not in order_data:
                            order_data[order.id] = {
                                'order_id': order.id,
                                'customer': order.user.email,
                                'total': str(order.total),
                                'ordered_at': timezone.localtime(order.created_at).isoformat(),
                                'items': []
                            }
                        order_data[order.id]['items'].append(food_data[-1])

                    # Create payment record
                    

                    # Create vendor payout
                    utc_now=timezone.now()
                    local_time=timezone.localtime(utc_now)
                    payout_date=local_time.date()-timedelta(days=1)
                    VendorPayout.objects.create(
                        vendor=vendor,
                       
                        order_data=list(order_data.values()),
                        food_data=food_data,
                        total_amount=total_amount,
                        commission=commission_rate,
                        net_amount=net_amount,
                        date=cutoff_date
                        
                        
                    )

                    # Mark items as processed
                    completed_items.update(
                        is_payout_processed=True,
                        processed_at=now_npt,
                        updated_at=now_npt
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Payout processing failed: {str(e)}'))
            raise 
