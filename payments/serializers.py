from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import (
    ShoppingCart, CartItem, Order, OrderItem, Payment, Refund,
    InstructorPayout, Revenue, Coupon, CouponUsage
)


class CartItemSerializer(serializers.ModelSerializer):
    """Shopping cart item serializer"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    instructor_name = serializers.CharField(source='course.instructor.full_name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = (
            'id', 'course', 'batch', 'course_title', 'course_thumbnail',
            'instructor_name', 'batch_name', 'unit_price', 'discount_amount',
            'total_price', 'added_at'
        )
        read_only_fields = ('id', 'unit_price', 'added_at')
    
    def validate(self, attrs):
        course = attrs['course']
        batch = attrs.get('batch')
        
        # Validate batch for structured courses
        if course.course_type == course.CourseType.STRUCTURED:
            if not batch:
                raise serializers.ValidationError("Batch is required for structured courses")
            if batch.course != course:
                raise serializers.ValidationError("Batch does not belong to this course")
            if not batch.is_enrollment_open:
                raise serializers.ValidationError("Enrollment is closed for this batch")
        elif batch:
            raise serializers.ValidationError("Batch is not applicable for self-paced courses")
        
        return attrs
    
    def create(self, validated_data):
        request = self.context['request']
        cart, created = ShoppingCart.objects.get_or_create(user=request.user)
        
        course = validated_data['course']
        batch = validated_data.get('batch')
        
        # Check if item already in cart
        existing_item = CartItem.objects.filter(
            cart=cart,
            course=course,
            batch=batch
        ).first()
        
        if existing_item:
            raise serializers.ValidationError("Item already in cart")
        
        # Set price from course or batch
        if batch and batch.price:
            unit_price = batch.price
        else:
            unit_price = course.price
        
        return CartItem.objects.create(
            cart=cart,
            course=course,
            batch=batch,
            unit_price=unit_price
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Shopping cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ShoppingCart
        fields = (
            'id', 'items', 'total_amount', 'item_count',
            'created_at', 'updated_at'
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.CharField(source='course.instructor.full_name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'course', 'batch', 'course_title', 'instructor_name',
            'unit_price', 'discount_amount', 'total_price', 'created_at'
        )


class OrderSerializer(serializers.ModelSerializer):
    """Order list serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'items', 'created_at',
            'completed_at'
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'user', 'status', 'subtotal',
            'discount_amount', 'tax_amount', 'total_amount',
            'coupon_code', 'coupon_discount_amount', 'billing_email',
            'billing_name', 'billing_address', 'items', 'created_at',
            'updated_at', 'completed_at'
        )


class OrderCreateSerializer(serializers.Serializer):
    """Order creation serializer"""
    billing_name = serializers.CharField(max_length=200)
    billing_email = serializers.EmailField()
    billing_address = serializers.JSONField(required=False, default=dict)
    coupon_code = serializers.CharField(max_length=50, required=False)
    
    def validate_coupon_code(self, value):
        if value:
            try:
                coupon = Coupon.objects.get(code=value)
                if not coupon.is_valid:
                    raise serializers.ValidationError("Coupon is not valid")
                return value
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code")
        return value
    
    def create(self, validated_data):
        request = self.context['request']
        
        # Get user's cart
        try:
            cart = ShoppingCart.objects.get(user=request.user)
        except ShoppingCart.DoesNotExist:
            raise serializers.ValidationError("Cart is empty")
        
        if not cart.items.exists():
            raise serializers.ValidationError("Cart is empty")
        
        # Calculate totals
        subtotal = cart.total_amount
        discount_amount = Decimal('0.00')
        coupon_discount_amount = Decimal('0.00')
        
        # Apply coupon if provided
        coupon = None
        coupon_code = validated_data.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid:
                    coupon_discount_amount = coupon.calculate_discount(subtotal)
            except Coupon.DoesNotExist:
                pass
        
        total_amount = subtotal - coupon_discount_amount
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            coupon_code=coupon_code or '',
            coupon_discount_amount=coupon_discount_amount,
            billing_name=validated_data['billing_name'],
            billing_email=validated_data['billing_email'],
            billing_address=validated_data.get('billing_address', {}),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Create order items from cart
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                course=cart_item.course,
                batch=cart_item.batch,
                unit_price=cart_item.unit_price,
                discount_amount=cart_item.discount_amount,
                total_price=cart_item.total_price,
                course_title=cart_item.course.title,
                instructor_name=cart_item.course.instructor.full_name or cart_item.course.instructor.username
            )
        
        # Record coupon usage
        if coupon and coupon_discount_amount > 0:
            CouponUsage.objects.create(
                coupon=coupon,
                user=request.user,
                order=order,
                discount_amount=coupon_discount_amount
            )
            
            # Update coupon usage count
            coupon.current_uses += 1
            coupon.save(update_fields=['current_uses'])
        
        # Clear cart
        cart.clear()
        
        return order


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id', 'payment_id', 'order_number', 'amount', 'currency',
            'payment_method', 'status', 'external_payment_id',
            'payment_gateway', 'failure_reason', 'created_at',
            'processed_at'
        )


class PaymentCreateSerializer(serializers.Serializer):
    """Payment creation serializer"""
    payment_method = serializers.ChoiceField(
        choices=Payment.PaymentMethod.choices
    )
    external_payment_id = serializers.CharField(max_length=100, required=False)
    gateway_response = serializers.JSONField(required=False, default=dict)
    
    def create(self, validated_data):
        order = self.context['order']
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            currency='USD',  # TODO: Make configurable
            payment_method=validated_data['payment_method'],
            external_payment_id=validated_data.get('external_payment_id', ''),
            gateway_response=validated_data.get('gateway_response', {})
        )
        
        return payment


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)
    
    class Meta:
        model = Refund
        fields = (
            'id', 'refund_id', 'order_number', 'amount', 'reason',
            'description', 'status', 'requested_by_name', 'processed_by_name',
            'created_at', 'processed_at'
        )


class RefundCreateSerializer(serializers.ModelSerializer):
    """Refund request serializer"""
    
    class Meta:
        model = Refund
        fields = ('reason', 'description')
    
    def create(self, validated_data):
        order = self.context['order']
        payment = self.context['payment']
        request = self.context['request']
        
        return Refund.objects.create(
            payment=payment,
            order=order,
            amount=payment.amount,
            reason=validated_data['reason'],
            description=validated_data.get('description', ''),
            requested_by=request.user
        )


class CouponSerializer(serializers.ModelSerializer):
    """Coupon serializer"""
    valid_status = serializers.ReadOnlyField(source='is_valid')
    
    class Meta:
        model = Coupon
        fields = (
            'id', 'code', 'name', 'description', 'coupon_type',
            'discount_percentage', 'discount_amount', 'max_uses',
            'max_uses_per_user', 'current_uses', 'valid_from',
            'valid_until', 'minimum_amount', 'status', 'is_public',
            'valid_status', 'created_at'
        )


class CouponCreateSerializer(serializers.ModelSerializer):
    """Coupon creation serializer"""
    
    class Meta:
        model = Coupon
        fields = (
            'code', 'name', 'description', 'coupon_type',
            'discount_percentage', 'discount_amount', 'max_uses',
            'max_uses_per_user', 'valid_from', 'valid_until',
            'minimum_amount', 'applicable_courses', 'is_public'
        )
    
    def validate(self, attrs):
        coupon_type = attrs['coupon_type']
        
        if coupon_type == Coupon.CouponType.PERCENTAGE:
            if not attrs.get('discount_percentage'):
                raise serializers.ValidationError("Discount percentage is required")
            if attrs['discount_percentage'] <= 0 or attrs['discount_percentage'] > 100:
                raise serializers.ValidationError("Discount percentage must be between 1 and 100")
        
        elif coupon_type == Coupon.CouponType.FIXED_AMOUNT:
            if not attrs.get('discount_amount'):
                raise serializers.ValidationError("Discount amount is required")
            if attrs['discount_amount'] <= 0:
                raise serializers.ValidationError("Discount amount must be greater than 0")
        
        if attrs['valid_from'] >= attrs['valid_until']:
            raise serializers.ValidationError("Valid from date must be before valid until date")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InstructorPayoutSerializer(serializers.ModelSerializer):
    """Instructor payout serializer"""
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    
    class Meta:
        model = InstructorPayout
        fields = (
            'id', 'payout_id', 'instructor_name', 'period_start',
            'period_end', 'gross_revenue', 'platform_commission',
            'commission_rate', 'net_amount', 'payout_method',
            'status', 'created_at', 'processed_at', 'notes'
        )


class RevenueSerializer(serializers.ModelSerializer):
    """Revenue tracking serializer"""
    course_title = serializers.CharField(source='order_item.course_title', read_only=True)
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    
    class Meta:
        model = Revenue
        fields = (
            'id', 'course_title', 'instructor_name', 'gross_amount',
            'platform_commission', 'instructor_earnings', 'commission_rate',
            'is_paid', 'created_at', 'paid_at'
        )


class CouponUsageSerializer(serializers.ModelSerializer):
    """Coupon usage tracking serializer"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = (
            'id', 'user_name', 'order_number', 'coupon_code',
            'discount_amount', 'used_at'
        )