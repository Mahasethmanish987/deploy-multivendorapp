from datetime import timedelta

import pytz
from accounts.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Q, Sum
from django.utils import timezone
from menu.models import FoodItem
from vendor.models import Vendor


class Payment(models.Model):
    choices = (
        ("complete", "completed"),
        ("canceled", "canceled"),
        ("pending", "pending"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100, choices=choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class Order(models.Model):
    STATUS = (
        ("new", "new"),
        ("pending", "pending"),
        ("accepted", "accepted"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, blank=True, null=True
    )
    vendors = models.ManyToManyField(Vendor, blank=True)
    order_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=50)
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    pin_code = models.CharField(max_length=50, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_data = models.JSONField(blank=True, null=True)
    payment_method = models.CharField(max_length=25)
    status = models.CharField(choices=STATUS, default="new", max_length=25)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def order_place_to(self):
        return " ,".join([str(i) for i in self.vendors.all()])

    def __str__(self):
        return self.order_number


class OrderedFood(models.Model):
    STATUS = (
        ("new", "new"),
        ("pending", "pending"),
        ("accepted", "accepted"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("cancelled_in_payment_gateway", "cancelled_in_payment_gateway"),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orders")
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, blank=True, null=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=STATUS, default="new", max_length=50)
    is_payout_processed = models.BooleanField(default=False)

    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    @classmethod
    def _get_earnings_queryset(cls, vendor=None):
        """Base queryset for completed orders (optional vendor filter)"""
        qs = cls.objects.filter(status="completed")
        if vendor:
            qs = qs.filter(fooditem__vendor=vendor)
        return qs

    @classmethod
    def todays_earnings(cls, vendor=None):
        """Earnings for TODAY (Kathmandu time)"""
        kathmandu_tz = pytz.timezone("Asia/Kathmandu")
        now_kathmandu = timezone.now().astimezone(kathmandu_tz)
        start_of_day = now_kathmandu.replace(hour=0, minute=0, second=0, microsecond=0)

        return (
            cls._get_earnings_queryset(vendor)
            .filter(created_at__gte=start_of_day)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

    @classmethod
    def weekly_earnings(cls, vendor=None):
        """Last 7 days earnings EXCLUDING today (Kathmandu time)"""
        kathmandu_tz = pytz.timezone("Asia/Kathmandu")
        now_kathmandu = timezone.now().astimezone(kathmandu_tz)

        # End of yesterday (23:59:59.999)
        end_date = (now_kathmandu - timedelta(days=1)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        # Start of 7 days ago (00:00:00)
        start_date = (end_date - timedelta(days=6)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return (
            cls._get_earnings_queryset(vendor)
            .filter(created_at__range=(start_date, end_date))
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

    @classmethod
    def monthly_earnings(cls, vendor=None):
        """Current month earnings EXCLUDING today (Kathmandu time)"""
        kathmandu_tz = pytz.timezone("Asia/Kathmandu")
        now_kathmandu = timezone.now().astimezone(kathmandu_tz)

        # First day of current month (00:00:00)
        first_day = now_kathmandu.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # End of yesterday (23:59:59.999)
        end_date = (now_kathmandu - timedelta(days=1)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        return (
            cls._get_earnings_queryset(vendor)
            .filter(created_at__range=(first_day, end_date))
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

    @classmethod
    def total_earnings(cls, vendor=None):
        """All-time earnings"""
        return (
            cls._get_earnings_queryset(vendor).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    @classmethod
    def all_months_earnings(cls, vendor=None):
        """Month-wise earnings breakdown (Kathmandu time)"""
        from django.db.models.functions import TruncMonth

        return (
            cls._get_earnings_queryset(vendor)
            .annotate(
                month=TruncMonth("created_at", tzinfo=pytz.timezone("Asia/Kathmandu"))
            )
            .values("month")
            .annotate(earnings=Sum("amount"))
            .order_by("month")
        )

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["order", "status"]),
        ]

    def time_since_creation(self):
        """Return duration since order creation"""
        return timezone.localtime() - self.created_at

    def is_nearing_expiry(self):
        """check if order is approaching 4 hour limit"""
        elasped = self.time_since_creation()
        return timedelta(minutes=2) < elasped < timedelta(minutes=4)

    def is_expired(self):
        return self.time_since_creation() >= timedelta(minutes=4)

    def __str__(self):
        return self.fooditem.food_title


class VendorPayout(models.Model):
    PAYOUT_STATUS = (
        ("pending", "pending"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="payouts")
    order_data = models.JSONField(help_text="structured order data at payout time")
    food_data = models.JSONField(help_text="food item data at payout time")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.15,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=PAYOUT_STATUS, default="pending")
    date = models.DateField(null=True, blank=True)
    payout_date = models.DateTimeField(null=True, blank=True)
    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vendor_payout",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    def save(self, *args, **kwargs):
        # Ensure net_amount is calculated before saving
        self.net_amount = self.total_amount * (1 - self.commission)
        super().save(*args, **kwargs)


class CustomerRefund(models.Model):
    """Tracks customer refunds for cancelled orders."""

    CHOICES = (
        ("pending", "pending"),
        ("completed", "completed"),
        ("failed", "failed"),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refunds")
    original_order = models.JSONField()
    refunded_items = models.JSONField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_reason = models.TextField(blank=True, null=True)
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="customer_refund",
        null=True,
        blank=True,
    )
    status = models.CharField(choices=CHOICES, default="pending")
    is_fully_cancelled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_eligibility(self):
        """Atomic check for full order cancellation"""

        order_id = self.original_order.get("id")
        if not order_id:
            return False

        active_count = (
            Order.objects.filter(id=order_id)
            .annotate(
                active=Count(
                    "orders", filter=~Q(orders__status__in=["cancelled", "completed"])
                )
            )
            .values_list("active", flat=True)
            .first()
            or 0
        )
        print('update eligibility')
        self.is_fully_cancelled = (active_count == 0)
        self.save(update_fields=["is_fully_cancelled"])
        return self.is_fully_cancelled

    @property
    def is_eligible_for_refund(self):
        return self.is_fully_cancelled
