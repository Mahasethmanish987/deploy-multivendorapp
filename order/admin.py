from django.contrib import admin

# Register your models here.
from django.utils.html import format_html
from django.core.exceptions import ValidationError

from .models import  Order, OrderedFood, Payment,VendorPayout,CustomerRefund


class OrderedFoodInline(admin.TabularInline):
    model = OrderedFood
    extra = 0
    readonly_fields = ("fooditem", "quantity", "price", "amount", "status")
    fields = ("fooditem", "quantity", "price", "amount", "status")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    fields = ("order_number", "user", "status", "total", "created_at")
    readonly_fields = ("order_number", "user", "status", "total", "created_at")
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "user",
        "amount",
        "status",
        "payment_orders",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("transaction_id", "user__email", "user__first_name")
    inlines = [OrderInline]
    date_hierarchy = "created_at"

    def payment_orders(self, obj):
        orders = obj.order_set.all()
        return format_html(
            "<br>".join([f"{o.order_number} ({o.status})" for o in orders])
        )

    payment_orders.short_description = "Related Orders"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "payment_status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_number", "user__email", "first_name", "last_name")
    inlines = [OrderedFoodInline]
    date_hierarchy = "created_at"
    readonly_fields = ("order_number", "created_at", "updated_at")
    fieldsets = (
        ("Order Information", {"fields": ("order_number", "user", "status", "total","total_data")}),
        ("Payment Details", {"fields": ("payment", "payment_method")}),
        (
            "Customer Information",
            {"fields": ("first_name", "last_name", "email", "phone")},
        ),
        ("Shipping Details", {"fields": ("address", "country", "state", "pin_code")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def payment_status(self, obj):
        if obj.payment:
            status_color = {
                "completed": "green",
                "pending": "orange",
                "failed": "red",
            }.get(obj.payment.status, "black")
            return format_html(
                '<span style="color: {};">{}</span>',
                status_color,
                obj.payment.status.upper(),
            )
        return "No Payment"

    payment_status.short_description = "Payment Status"


@admin.register(OrderedFood)
class OrderedFoodAdmin(admin.ModelAdmin):
    list_display = ("fooditem", "order_link", "quantity", "price", "amount", "status",'is_payout_processed')
    list_filter = ("status", "created_at")
    search_fields = ("order__order_number", "fooditem__food_title")
    readonly_fields = ("order", "user", "fooditem", "quantity", "price", "amount")
    date_hierarchy = "created_at"

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/orders/order/{}/change/">{}</a>',
            obj.order.id,
            obj.order.order_number,
        )

    order_link.short_description = "Order Number"




@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = (
        'vendor', 'payout_date', 'total_amount', 
        'commission', 'net_amount', 'status', 'payment_status'
    )
    list_filter = ('status', 'payout_date')
    search_fields = ('vendor__name', 'payout_date')
    readonly_fields = ('created_at', 'updated_at', 'payment_status')
    fieldsets = (
        (None, {
            'fields': (
                'vendor','date', 'payout_date', 'status',
                ('total_amount', 'commission', 'net_amount'),
                'payment'
            )
        }),
        ('Historical Data', {
            'fields': ('order_data', 'food_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def payment_status(self, obj):
        if obj.payment:
            return format_html(
                '<span style="color: {};">{}</span>',
                'green' if obj.payment.status=='complete' else 'red',
                obj.payment.status
            )
        return "No Payment"
    payment_status.short_description = 'Payment Status'

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj and obj.status in ['completed', 'cancelled']:
            return readonly + ('total_amount', 'commission', 'net_amount', 'vendor', 'payout_date')
        return readonly

    def save_model(self, request, obj, form, change):
        if change:
            original = VendorPayout.objects.get(pk=obj.pk)
            if original.status in ['completed', 'cancelled']:
                protected_fields = ['total_amount', 'commission', 'net_amount']
                for field in protected_fields:
                    if getattr(obj, field) != getattr(original, field):
                        raise ValidationError(
                            f"Cannot modify {field} for {original.status} payouts"
                        )
        super().save_model(request, obj, form, change)

@admin.register(CustomerRefund)
class CustomerRefundAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'truncated_reason', 'refund_amount',
        'status', 'is_eligible', 'payment_status'
    )
    list_filter = ('status', 'is_fully_cancelled')
    search_fields = ('customer__email', 'customer__username', 'original_order__id')
    readonly_fields = ('created_at', 'updated_at', 'is_eligible')
    actions = ('update_eligibility',)
    fieldsets = (
        (None, {
            'fields': (
                'customer', 'original_order', 'refunded_items',
                ('refund_amount', 'status'), 'payment'
            )
        }),
        ('Cancellation Details', {
            'fields': ('refund_reason', 'is_fully_cancelled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def truncated_reason(self, obj):
        return obj.refund_reason[:50] + '...' if obj.refund_reason else ''
    truncated_reason.short_description = 'Reason'

    def payment_status(self, obj):
        if obj.payment:
            return format_html(
                '<span style="color: {};">{}</span>',
                'green' if obj.payment.status=='complete' else 'red',
                obj.payment.status
            )
        return "No Payment"
    payment_status.short_description = 'Payment Status'

    @admin.display(boolean=True, description='Eligible?')
    def is_eligible(self, obj):
        return obj.is_eligible_for_refund

    @admin.display(boolean=True, description='Eligible?')
    def is_eligible(self, obj):
        return obj.is_eligible_for_refund

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Auto-update eligibility after saving
        obj.update_eligibility()

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj and obj.status == 'completed':
            return readonly + ('refund_amount', 'original_order', 'refunded_items')
        return readonly
