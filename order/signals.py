from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import CustomerRefund, OrderedFood


@receiver(post_save, sender=OrderedFood)
def handle_immediate_refunds(sender, instance, **kwargs):
    """
    Processes refunds atomically when food items are cancelled,
    tracking only vendors of cancelled items in order snapshot.
    """
    if instance.status not in ["cancelled","completed"] or kwargs.get("created", False):
        return
    
    elif instance.status=='completed':
        order=instance.order 
        existing_refund = CustomerRefund.objects.filter(
                original_order__id=order.id
            ).first()
        if existing_refund:
              existing_refund.update_eligibility()
        return 

   
    # Prepare food item snapshot with vendor
    food_data = {
        "id": instance.id,
        "food_title": instance.fooditem.food_title,
        "vendor_name": instance.fooditem.vendor.vendor_name,
        "quantity": instance.quantity,
        "price": str(instance.price),
        "amount": str(instance.amount),
        "cancelled_at": timezone.localtime(timezone.now()).isoformat(),
    }

    with transaction.atomic():
        try:
            order = instance.order
           

            # Get existing vendors from previous refunds (if any)
            existing_vendors = set()
            amount = 0
            existing_refund = CustomerRefund.objects.filter(
                original_order__id=order.id
            ).first()

            if existing_refund:
                existing_vendors = set(
                    existing_refund.original_order.get("vendors", [])
                )
                amount = Decimal(existing_refund.original_order.get("total_amount", 0))

            # Add current item's vendor to the set
            current_vendor = instance.fooditem.vendor.vendor_name
            updated_vendors = list(existing_vendors.union({current_vendor}))
            amount += instance.amount

            # Create order snapshot with updated vendor list
            order_snapshot = {
                "order_number": order.order_number,
                "id": order.id,
                "total_amount": str(amount),
                "created_at": timezone.localtime(order.created_at).isoformat(),
                "customer": {"id": order.user.id, "email": order.user.email},
                "vendors": updated_vendors,  # Unique vendors from all cancelled items
            }

            # Get or create refund with atomic update
            refund, created = CustomerRefund.objects.select_for_update().get_or_create(
                original_order__id=order.id,
                defaults={
                    "customer": order.user,
                    "original_order": order_snapshot,
                    "refunded_items": [food_data],
                    "refund_amount": instance.amount,
                    "status": "pending",
                },
            )

            if not created:
                # Update both refund items and vendor list atomically
                CustomerRefund.objects.filter(id=refund.id).update(
                    refunded_items=refund.refunded_items + [food_data],
                    refund_amount=F("refund_amount") + instance.amount,
                    original_order=order_snapshot,  # Update vendor list
                    updated_at=timezone.now(),
                )
            refund.update_eligibility()

        except Exception as e:
            if "refund" in locals():
                refund.status = "failed"
                refund.save()
            raise e
