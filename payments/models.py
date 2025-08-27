from django.db import models
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ShoppingCart(models.Model):
    """Shopping cart for course purchases"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    if TYPE_CHECKING:
        items: 'QuerySet[CartItem]'
    
    class Meta:
        db_table = 'shopping_carts'
    
    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def item_count(self):
        return self.items.count()
    
    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Items in shopping cart"""
    
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='cart_items')
    batch = models.ForeignKey(
        'courses.CourseBatch', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='cart_items'
    )
    
    # Pricing at time of adding to cart
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'course', 'batch']
    
    def __str__(self):
        return f"{self.course.title} in cart for {self.cart.user.email}"
    
    @property
    def total_price(self):
        return self.unit_price - self.discount_amount


class Order(models.Model):
    """Orders for course purchases"""
    
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Payment'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
    
    # Order identification
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Discount/Coupon information
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Billing information
    billing_email = models.EmailField()
    billing_name = models.CharField(max_length=200)
    billing_address = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} by {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        if self.status == self.OrderStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        import uuid
        return f"ORD{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class OrderItem(models.Model):
    """Items in an order"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='order_items')
    batch = models.ForeignKey(
        'courses.CourseBatch', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='order_items'
    )
    
    # Pricing at time of purchase
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Course information at time of purchase (for historical records)
    course_title = models.CharField(max_length=200)
    instructor_name = models.CharField(max_length=200)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
        unique_together = ['order', 'course', 'batch']
    
    def __str__(self):
        return f"{self.course_title} - Order {self.order.order_number}"


class Payment(models.Model):
    """Payment transactions"""
    
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        E_WALLET = 'e_wallet', 'E-Wallet'
        VIRTUAL_ACCOUNT = 'virtual_account', 'Virtual Account'
        PAYPAL = 'paypal', 'PayPal'
        STRIPE = 'stripe', 'Stripe'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
        PARTIALLY_REFUNDED = 'partially_refunded', 'Partially Refunded'
    
    # Payment identification
    payment_id = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    
    # External payment system integration
    external_payment_id = models.CharField(max_length=100, blank=True)
    payment_gateway = models.CharField(max_length=50, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Failure information
    failure_reason = models.TextField(blank=True)
    failure_code = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['external_payment_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = self.generate_payment_id()
        
        if self.status == self.PaymentStatus.COMPLETED and not self.processed_at:
            self.processed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_payment_id(self):
        """Generate unique payment ID"""
        import uuid
        return f"PAY{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class Refund(models.Model):
    """Refund transactions"""
    
    class RefundStatus(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
    
    class RefundReason(models.TextChoices):
        CUSTOMER_REQUEST = 'customer_request', 'Customer Request'
        COURSE_CANCELLED = 'course_cancelled', 'Course Cancelled'
        TECHNICAL_ISSUE = 'technical_issue', 'Technical Issue'
        POLICY_VIOLATION = 'policy_violation', 'Policy Violation'
        OTHER = 'other', 'Other'
    
    # Refund identification
    refund_id = models.CharField(max_length=50, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=RefundReason.choices)
    description = models.TextField(blank=True)
    
    # Status and processing
    status = models.CharField(max_length=20, choices=RefundStatus.choices, default=RefundStatus.REQUESTED)
    
    # External refund processing
    external_refund_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Processing information
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='requested_refunds'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['refund_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment']),
        ]
    
    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.refund_id:
            self.refund_id = self.generate_refund_id()
        super().save(*args, **kwargs)
    
    def generate_refund_id(self):
        """Generate unique refund ID"""
        import uuid
        return f"REF{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class InstructorPayout(models.Model):
    """Instructor payouts and earnings"""
    
    class PayoutStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    # Payout identification
    payout_id = models.CharField(max_length=50, unique=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payouts'
    )
    
    # Payout period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Financial details
    gross_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4)  # e.g., 0.1000 for 10%
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payout method
    payout_method = models.CharField(max_length=50)  # 'bank_transfer', 'paypal', etc.
    payout_details = models.JSONField(default=dict, blank=True)  # Bank/PayPal details
    
    # Status and processing
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    
    # External payout processing
    external_payout_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Processing information
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payouts'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'instructor_payouts'
        ordering = ['-created_at']
        unique_together = ['instructor', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['payout_id']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"Payout {self.payout_id} to {self.instructor.email}"
    
    def save(self, *args, **kwargs):
        if not self.payout_id:
            self.payout_id = self.generate_payout_id()
        
        # Calculate net amount
        self.net_amount = self.gross_revenue - self.platform_commission
        
        super().save(*args, **kwargs)
    
    def generate_payout_id(self):
        """Generate unique payout ID"""
        import uuid
        return f"PO{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class Revenue(models.Model):
    """Revenue tracking for courses and instructors"""
    
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='revenue')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='revenues'
    )
    
    # Revenue breakdown
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    instructor_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Payout tracking
    payout = models.ForeignKey(
        InstructorPayout, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='revenue_items'
    )
    is_paid = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'revenues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instructor', 'is_paid']),
            models.Index(fields=['created_at']),
            models.Index(fields=['payout']),
        ]
    
    def __str__(self):
        return f"Revenue from {self.order_item.course_title} - {self.instructor_earnings}"


class Coupon(models.Model):
    """Discount coupons for courses"""
    
    class CouponType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage Discount'
        FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount Discount'
        FREE_COURSE = 'free_course', 'Free Course'
    
    class CouponStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        EXPIRED = 'expired', 'Expired'
    
    # Coupon identification
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Discount settings
    coupon_type = models.CharField(max_length=20, choices=CouponType.choices)
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Usage limits
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_user = models.IntegerField(default=1)
    current_uses = models.IntegerField(default=0)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Applicable courses (empty means all courses)
    applicable_courses = models.ManyToManyField('courses.Course', blank=True, related_name='coupons')
    
    # Minimum purchase requirements
    minimum_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Status
    status = models.CharField(max_length=20, choices=CouponStatus.choices, default=CouponStatus.ACTIVE)
    is_public = models.BooleanField(default=True)  # Can be found by users or admin-only
    
    # Created by (instructor can create coupons for their courses)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_coupons'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'valid_from', 'valid_until']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"Coupon {self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        return (
            self.status == self.CouponStatus.ACTIVE and
            self.valid_from <= now <= self.valid_until and
            (self.max_uses is None or self.current_uses < self.max_uses)
        )
    
    def calculate_discount(self, amount):
        """Calculate discount amount for given order amount"""
        if not self.is_valid or amount < self.minimum_amount:
            return Decimal('0.00')
        
        if self.coupon_type == self.CouponType.PERCENTAGE:
            return min(amount * (self.discount_percentage / 100), amount)
        elif self.coupon_type == self.CouponType.FIXED_AMOUNT:
            return min(self.discount_amount, amount)
        elif self.coupon_type == self.CouponType.FREE_COURSE:
            return amount
        
        return Decimal('0.00')


class CouponUsage(models.Model):
    """Track coupon usage"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_usages')
    
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coupon_usages'
        unique_together = ['coupon', 'order']
        indexes = [
            models.Index(fields=['coupon', 'user']),
            models.Index(fields=['used_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"