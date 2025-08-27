"""
Admin interface for financial management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ShoppingCart, CartItem, Order, OrderItem, Payment, Refund,
    InstructorPayout, Revenue, Coupon, CouponUsage
)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'total_amount', 
        'created_at', 'completed_at'
    ]
    list_filter = ['status', 'created_at', 'completed_at']
    search_fields = ['order_number', 'user__email', 'user__username']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'user', 'status', 
                'subtotal', 'discount_amount', 'tax_amount', 'total_amount'
            )
        }),
        ('Coupon Information', {
            'fields': ('coupon_code', 'coupon_discount_amount'),
            'classes': ('collapse',)
        }),
        ('Billing Information', {
            'fields': ('billing_email', 'billing_name', 'billing_address'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('user_agent', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_id', 'order_link', 'amount', 'currency', 
        'payment_method', 'status', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'currency', 'created_at']
    search_fields = [
        'payment_id', 'external_payment_id', 
        'order__order_number', 'order__user__email'
    ]
    readonly_fields = ['payment_id', 'created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_id', 'order', 'amount', 'currency', 
                'payment_method', 'status'
            )
        }),
        ('External Integration', {
            'fields': ('external_payment_id', 'payment_gateway', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Failure Information', {
            'fields': ('failure_reason', 'failure_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:payments_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Order'  # type: ignore

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'refund_id', 'payment_link', 'amount', 'reason', 
        'status', 'requested_by', 'created_at'
    ]
    list_filter = ['reason', 'status', 'created_at']
    search_fields = [
        'refund_id', 'payment__payment_id', 
        'payment__order__order_number', 'requested_by__email'
    ]
    readonly_fields = ['refund_id', 'created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Refund Information', {
            'fields': (
                'refund_id', 'payment', 'order', 'amount', 
                'reason', 'description', 'status'
            )
        }),
        ('Processing Information', {
            'fields': ('requested_by', 'processed_by', 'processed_at'),
        }),
        ('External Integration', {
            'fields': ('external_refund_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def payment_link(self, obj):
        if obj.payment:
            url = reverse('admin:payments_payment_change', args=[obj.payment.id])
            return format_html('<a href="{}">{}</a>', url, obj.payment.payment_id)
        return '-'
    payment_link.short_description = 'Payment'  # type: ignore
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'payment', 'order', 'requested_by', 'processed_by'
        )


@admin.register(InstructorPayout)
class InstructorPayoutAdmin(admin.ModelAdmin):
    list_display = [
        'payout_id', 'instructor', 'period', 'gross_revenue', 
        'net_amount', 'status', 'created_at'
    ]
    list_filter = ['status', 'payout_method', 'created_at']
    search_fields = [
        'payout_id', 'instructor__email', 'instructor__username'
    ]
    readonly_fields = ['payout_id', 'created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payout Information', {
            'fields': (
                'payout_id', 'instructor', 'period_start', 'period_end',
                'gross_revenue', 'platform_commission', 'commission_rate',
                'net_amount', 'status'
            )
        }),
        ('Payout Method', {
            'fields': ('payout_method', 'payout_details'),
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'processed_at', 'notes'),
        }),
        ('External Integration', {
            'fields': ('external_payout_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def period(self, obj):
        return f"{obj.period_start} to {obj.period_end}"
    period.short_description = 'Payout Period'  # type: ignore
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('instructor', 'processed_by')


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = [
        'order_item', 'instructor', 'gross_amount', 
        'instructor_earnings', 'is_paid', 'created_at'
    ]
    list_filter = ['is_paid', 'created_at']
    search_fields = [
        'order_item__course_title', 'instructor__email', 'instructor__username'
    ]
    readonly_fields = ['created_at', 'paid_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Revenue Information', {
            'fields': (
                'order_item', 'instructor', 'gross_amount',
                'platform_commission', 'instructor_earnings', 
                'commission_rate'
            )
        }),
        ('Payout Information', {
            'fields': ('payout', 'is_paid', 'paid_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order_item', 'instructor', 'payout'
        )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'coupon_type', 'discount_display', 
        'validity_period', 'current_uses', 'max_uses', 'status'
    ]
    list_filter = ['coupon_type', 'status', 'is_public', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'name', 'description', 'created_by'),
        }),
        ('Discount Settings', {
            'fields': (
                'coupon_type', 'discount_percentage', 
                'discount_amount'
            ),
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'max_uses_per_user', 'current_uses'),
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until'),
        }),
        ('Applicability', {
            'fields': ('applicable_courses', 'minimum_amount', 'is_public'),
        }),
        ('Status', {
            'fields': ('status',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def discount_display(self, obj):
        if obj.coupon_type == obj.CouponType.PERCENTAGE:
            return f"{obj.discount_percentage}%"
        elif obj.coupon_type == obj.CouponType.FIXED_AMOUNT:
            return f"{obj.discount_amount}"
        elif obj.coupon_type == obj.CouponType.FREE_COURSE:
            return "Free Course"
        return "-"
    discount_display.short_description = 'Discount'  # type: ignore
    
    def validity_period(self, obj):
        return f"{obj.valid_from.strftime('%Y-%m-%d')} to {obj.valid_until.strftime('%Y-%m-%d')}"
    validity_period.short_description = 'Validity Period'  # type: ignore
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('applicable_courses')


# Register other models with basic admin interface
@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'  # type: ignore


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'course', 'batch', 'unit_price', 'added_at']
    list_filter = ['added_at']
    search_fields = [
        'cart__user__email', 'course__title'
    ]
    readonly_fields = ['added_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'course_title', 'instructor_name', 
        'unit_price', 'total_price', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = [
        'order__order_number', 'course_title', 'instructor_name'
    ]
    readonly_fields = ['created_at']


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'discount_amount', 'used_at']
    list_filter = ['used_at']
    search_fields = [
        'coupon__code', 'user__email', 'order__order_number'
    ]
    readonly_fields = ['used_at']