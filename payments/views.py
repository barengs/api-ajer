from rest_framework import generics, permissions, status, serializers
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from decimal import Decimal

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    ShoppingCart, CartItem, Order, OrderItem, Payment, Refund,
    InstructorPayout, Revenue, Coupon, CouponUsage
)
from .serializers import (
    ShoppingCartSerializer, CartItemSerializer, OrderSerializer,
    OrderDetailSerializer, OrderCreateSerializer, PaymentSerializer,
    PaymentCreateSerializer, RefundSerializer, RefundCreateSerializer,
    CouponSerializer, CouponCreateSerializer, InstructorPayoutSerializer,
    RevenueSerializer
)
from courses.models import Course, Enrollment
from accounts.models import User


@extend_schema(
    tags=['Payments'],
    summary='Keranjang Belanja',
    description='''
    Mendapatkan shopping cart user yang sedang login.
    
    **Auto-Create Cart:**
    Jika user belum memiliki cart, sistem akan otomatis
    membuat cart baru untuk user tersebut.
    
    **Cart Information:**
    - Daftar semua items dalam cart
    - Total harga sebelum dan sesudah diskon
    - Informasi kupon yang digunakan
    - Detail setiap course dalam cart
    
    **Real-time Updates:**
    Cart selalu menampilkan informasi terkini termasuk
    harga course yang mungkin berubah.
    ''',
    responses={
        200: {
            'description': 'Shopping cart berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'user': {
                            'id': 1,
                            'full_name': 'John Doe'
                        },
                        'items': [
                            {
                                'id': 1,
                                'course': {
                                    'id': 1,
                                    'title': 'Python untuk Pemula',
                                    'thumbnail': 'http://localhost:8000/media/course_thumbnails/python.jpg',
                                    'instructor': {
                                        'full_name': 'Dr. Jane Smith'
                                    }
                                },
                                'batch': {
                                    'id': 1,
                                    'name': 'Batch Januari 2024',
                                    'start_date': '2024-01-20'
                                },
                                'price': '299000.00',
                                'added_at': '2024-01-15T10:30:00Z'
                            }
                        ],
                        'items_count': 1,
                        'subtotal': '299000.00',
                        'discount_amount': '29900.00',
                        'total_amount': '269100.00',
                        'applied_coupon': {
                            'code': 'WELCOME10',
                            'discount_percent': 10
                        },
                        'updated_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        }
    }
)
class ShoppingCartView(generics.RetrieveAPIView):
    """Get user's shopping cart"""
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ShoppingCart.objects.all()
    
    def get_object(self) -> ShoppingCart:  # type: ignore[override]
        cart, created = ShoppingCart.objects.get_or_create(user=self.request.user)
        return cart


@extend_schema(
    tags=['Payments'],
    summary='Tambah ke Keranjang',
    description='''
    Menambahkan course ke shopping cart user.
    
    **Validasi sebelum menambah:**
    1. User belum enrolled di course tersebut
    2. Course masih tersedia untuk pembelian
    3. Untuk structured course: batch masih open untuk enrollment
    4. Course belum ada di cart (prevent duplicate)
    
    **Auto Cart Creation:**
    Jika user belum memiliki cart, akan otomatis dibuat.
    
    **Batch Selection:**
    Untuk structured course, user harus memilih batch
    yang akan diikuti saat enrollment.
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'course': {
                    'type': 'integer',
                    'description': 'ID course yang akan ditambahkan'
                },
                'batch': {
                    'type': 'integer',
                    'description': 'ID batch untuk structured course (opsional)'
                }
            },
            'required': ['course']
        }
    },
    examples=[
        OpenApiExample(
            'Self-paced Course',
            value={
                'course': 1
            },
            request_only=True
        ),
        OpenApiExample(
            'Structured Course',
            value={
                'course': 2,
                'batch': 1
            },
            request_only=True
        )
    ],
    responses={
        201: {
            'description': 'Item berhasil ditambahkan ke cart',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'course': {
                            'id': 1,
                            'title': 'Python untuk Pemula',
                            'price': '299000.00'
                        },
                        'batch': None,
                        'price': '299000.00',
                        'added_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Sudah enrolled atau sudah di cart',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are already enrolled in this course'
                    }
                }
            }
        }
    }
)
class CartItemCreateView(generics.CreateAPIView):
    """Add item to shopping cart"""
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        
        # Check if user is already enrolled
        if Enrollment.objects.filter(
            student=self.request.user,
            course=course,
            is_active=True
        ).exists():
            raise serializers.ValidationError("You are already enrolled in this course")
        
        serializer.save()


class CartItemDeleteView(generics.DestroyAPIView):
    """Remove item from shopping cart"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = CartItem.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        return CartItem.objects.filter(cart__user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def clear_cart(request):
    """Clear all items from shopping cart"""
    try:
        cart = ShoppingCart.objects.get(user=request.user)
        cart.clear()
        return Response({'message': 'Cart cleared successfully'})
    except ShoppingCart.DoesNotExist:
        return Response({'message': 'Cart is already empty'})


@extend_schema(
    tags=['Payments'],
    summary='Validasi Kupon',
    description='''
    Memvalidasi kode kupon dan menghitung diskon yang dapat diperoleh.
    
    **Validasi yang dilakukan:**
    1. Kupon code valid dan masih aktif
    2. Belum expired
    3. User belum melebihi batas usage per user
    4. Cart total memenuhi minimum amount
    5. Cart tidak kosong
    
    **Response Information:**
    - Status validitas kupon
    - Detail kupon (tipe, value, expired date)
    - Jumlah diskon yang akan diperoleh
    - Total akhir setelah diskon
    
    **Coupon Types:**
    - Percentage: Diskon persentase (contoh: 10%)
    - Fixed Amount: Diskon nominal tetap (contoh: Rp 50.000)
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'coupon_code': {
                    'type': 'string',
                    'description': 'Kode kupon yang akan divalidasi',
                    'example': 'WELCOME10'
                }
            },
            'required': ['coupon_code']
        }
    },
    responses={
        200: {
            'description': 'Kupon valid dan dapat digunakan',
            'content': {
                'application/json': {
                    'example': {
                        'valid': True,
                        'coupon': {
                            'id': 1,
                            'code': 'WELCOME10',
                            'discount_type': 'percentage',
                            'discount_value': 10.0,
                            'minimum_amount': '100000.00',
                            'valid_until': '2024-02-29T23:59:59Z',
                            'description': 'Diskon 10% untuk user baru'
                        },
                        'discount_amount': '29900.00',
                        'final_total': '269100.00'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Kupon tidak valid',
            'content': {
                'application/json': {
                    'examples': {
                        'invalid_code': {
                            'summary': 'Kode kupon tidak valid',
                            'value': {'error': 'Invalid coupon code'}
                        },
                        'expired': {
                            'summary': 'Kupon sudah expired',
                            'value': {'error': 'Coupon is not valid or expired'}
                        },
                        'usage_limit': {
                            'summary': 'Batas usage tercapai',
                            'value': {'error': 'Coupon usage limit exceeded'}
                        },
                        'minimum_amount': {
                            'summary': 'Minimum amount tidak terpenuhi',
                            'value': {'error': 'Minimum order amount of $100000 required'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_coupon(request):
    """Validate coupon code"""
    coupon_code = request.data.get('coupon_code')
    if not coupon_code:
        return Response(
            {'error': 'Coupon code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        coupon = Coupon.objects.get(code=coupon_code)
        
        if not coupon.is_valid:
            return Response(
                {'error': 'Coupon is not valid or expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check usage limits
        user_usage_count = CouponUsage.objects.filter(
            coupon=coupon,
            user=request.user
        ).count()
        
        if user_usage_count >= coupon.max_uses_per_user:
            return Response(
                {'error': 'Coupon usage limit exceeded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get cart total to calculate discount
        try:
            cart = ShoppingCart.objects.get(user=request.user)
            cart_total = cart.total_amount
            
            if cart_total < coupon.minimum_amount:
                return Response(
                    {'error': f'Minimum order amount of ${coupon.minimum_amount} required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            discount_amount = coupon.calculate_discount(cart_total)
            
            return Response({
                'valid': True,
                'coupon': CouponSerializer(coupon).data,
                'discount_amount': discount_amount,
                'final_total': cart_total - discount_amount
            })
            
        except ShoppingCart.DoesNotExist:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Invalid coupon code'},
            status=status.HTTP_400_BAD_REQUEST
        )


class OrderCreateView(generics.CreateAPIView):
    """Create new order from cart"""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderListView(generics.ListAPIView):
    """List user's orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items').order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """Get order details"""
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


@extend_schema(
    tags=['Payments'],
    summary='Proses Pembayaran',
    description='''
    Memproses pembayaran untuk order yang pending.
    
    **Payment Flow:**
    1. Validasi order status = PENDING
    2. Process payment dengan gateway (Stripe, dll)
    3. Update payment status berdasarkan hasil
    4. Jika sukses: create enrollments dan revenue records
    5. Jika gagal: update status dan return error
    
    **Integration dengan Payment Gateway:**
    Dalam implementasi production, endpoint ini akan
    terintegrasi dengan Stripe, PayPal, atau gateway lainnya.
    
    **Auto Enrollment:**
    Setelah payment sukses, user otomatis enrolled
    ke semua course dalam order.
    
    **Revenue Tracking:**
    Sistem akan mencatat revenue dan commission
    untuk instructor dan platform.
    ''',
    parameters=[
        OpenApiParameter(
            name='order_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID order yang akan dibayar'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'payment_method': {
                    'type': 'string',
                    'enum': ['credit_card', 'bank_transfer', 'e_wallet'],
                    'description': 'Metode pembayaran'
                },
                'payment_details': {
                    'type': 'object',
                    'description': 'Detail pembayaran (card token, bank account, dll)'
                }
            },
            'required': ['payment_method']
        }
    },
    examples=[
        OpenApiExample(
            'Credit Card Payment',
            value={
                'payment_method': 'credit_card',
                'payment_details': {
                    'card_token': 'tok_visa_4242424242424242',
                    'save_card': True
                }
            },
            request_only=True
        ),
        OpenApiExample(
            'Bank Transfer',
            value={
                'payment_method': 'bank_transfer',
                'payment_details': {
                    'bank_code': 'BCA',
                    'account_number': '1234567890'
                }
            },
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Pembayaran berhasil diproses',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Payment processed successfully',
                        'payment': {
                            'id': 1,
                            'status': 'completed',
                            'amount': '269100.00',
                            'payment_method': 'credit_card',
                            'processed_at': '2024-01-15T11:00:00Z',
                            'transaction_id': 'ch_1234567890'
                        },
                        'order': {
                            'id': 1,
                            'order_number': 'ORD-2024-001',
                            'status': 'completed',
                            'total_amount': '269100.00',
                            'completed_at': '2024-01-15T11:00:00Z'
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Payment processing failed',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Payment processing failed'
                    }
                }
            }
        },
        404: {
            'description': 'Order tidak ditemukan atau bukan milik user'
        }
    }
)
class PaymentCreateView(generics.CreateAPIView):
    """Process payment for order"""
    serializer_class = PaymentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user,
            status=Order.OrderStatus.PENDING
        )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'order': order}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        
        # In a real implementation, integrate with payment gateway here
        # For demo purposes, we'll mark payment as completed
        success = self._process_payment(payment, request.data)
        
        if success:
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.processed_at = timezone.now()
            payment.save()
            
            # Complete order
            order.status = Order.OrderStatus.COMPLETED
            order.completed_at = timezone.now()
            order.save()
            
            # Create enrollments
            self._create_enrollments(order)
            
            # Create revenue records
            self._create_revenue_records(order)
            
            return Response({
                'message': 'Payment processed successfully',
                'payment': PaymentSerializer(payment).data,
                'order': OrderDetailSerializer(order).data
            })
        else:
            payment.status = Payment.PaymentStatus.FAILED
            payment.failure_reason = 'Payment processing failed'
            payment.save()
            
            order.status = Order.OrderStatus.FAILED
            order.save()
            
            return Response(
                {'error': 'Payment processing failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _process_payment(self, payment, payment_data):
        """Process payment with gateway (mock implementation)"""
        # In a real implementation, integrate with Stripe, PayPal, etc.
        # For demo purposes, assume all payments succeed
        return True
    
    def _create_enrollments(self, order):
        """Create course enrollments for completed order"""
        for item in order.items.all():
            enrollment, created = Enrollment.objects.get_or_create(
                student=order.user,
                course=item.course,
                defaults={
                    'batch': item.batch,
                    'amount_paid': item.total_price,
                    'payment_method': 'online',
                    'transaction_id': order.order_number
                }
            )
            
            # Update course enrollment count
            if created:
                item.course.total_enrollments += 1
                item.course.save(update_fields=['total_enrollments'])
                
                # Update batch enrollment count for structured courses
                if item.batch:
                    item.batch.current_enrollments += 1
                    item.batch.save(update_fields=['current_enrollments'])
    
    def _create_revenue_records(self, order):
        """Create revenue tracking records"""
        from django.conf import settings
        commission_rate = Decimal(str(settings.PLATFORM_COMMISSION_RATE))
        
        for item in order.items.all():
            platform_commission = item.total_price * commission_rate
            instructor_earnings = item.total_price - platform_commission
            
            Revenue.objects.create(
                order_item=item,
                instructor=item.course.instructor,
                gross_amount=item.total_price,
                platform_commission=platform_commission,
                instructor_earnings=instructor_earnings,
                commission_rate=commission_rate
            )


class PaymentListView(generics.ListAPIView):
    """List user's payments"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        return Payment.objects.filter(
            order__user=self.request.user
        ).select_related('order').order_by('-created_at')


class RefundRequestView(generics.CreateAPIView):
    """Request refund for payment"""
    serializer_class = RefundCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        payment_id = kwargs.get('payment_id')
        payment = get_object_or_404(
            Payment,
            id=payment_id,
            order__user=request.user,
            status=Payment.PaymentStatus.COMPLETED
        )
        
        # Check if refund already requested
        if Refund.objects.filter(
            payment=payment,
            status__in=[Refund.RefundStatus.REQUESTED, Refund.RefundStatus.PROCESSING]
        ).exists():
            return Response(
                {'error': 'Refund already requested for this payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={
                'order': payment.order,
                'payment': payment,
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        refund = serializer.save()
        
        return Response(
            RefundSerializer(refund).data,
            status=status.HTTP_201_CREATED
        )


class RefundListView(generics.ListAPIView):
    """List user's refunds"""
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Refund.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        return Refund.objects.filter(
            order__user=self.request.user
        ).select_related('order', 'requested_by', 'processed_by').order_by('-created_at')


# Instructor Views

class InstructorRevenueView(generics.ListAPIView):
    """Instructor revenue tracking"""
    serializer_class = RevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Revenue.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) != User.UserRole.INSTRUCTOR:
            return Revenue.objects.none()
        
        return Revenue.objects.filter(
            instructor=self.request.user
        ).select_related('order_item', 'instructor').order_by('-created_at')


class InstructorPayoutListView(generics.ListAPIView):
    """Instructor payout history"""
    serializer_class = InstructorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = InstructorPayout.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) != User.UserRole.INSTRUCTOR:
            return InstructorPayout.objects.none()
        
        return InstructorPayout.objects.filter(
            instructor=self.request.user
        ).order_by('-created_at')


@extend_schema(
    tags=['Payments'],
    summary='Ringkasan Penghasilan Instructor',
    description='''
    Mendapatkan ringkasan lengkap penghasilan instructor.
    
    **Metrics yang disediakan:**
    - Total revenue dari semua penjualan
    - Total earnings setelah dipotong komisi platform
    - Total komisi platform
    - Earnings yang sudah dibayarkan
    - Earnings yang masih pending
    - Total jumlah penjualan
    - Penghasilan bulan ini
    
    **Commission System:**
    Platform mengambil komisi dari setiap penjualan,
    sisanya menjadi earnings instructor.
    
    **Dashboard Analytics:**
    Data ini berguna untuk instructor dashboard
    dan financial reporting.
    ''',
    responses={
        200: {
            'description': 'Ringkasan penghasilan berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'total_revenue': '2500000.00',
                        'total_earnings': '2125000.00',
                        'platform_commission': '375000.00',
                        'paid_earnings': '1500000.00',
                        'pending_earnings': '625000.00',
                        'total_sales': 25,
                        'this_month_earnings': '450000.00'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Hanya instructor yang dapat melihat earnings',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Only instructors can view earnings'
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def instructor_earnings_summary(request):
    """Get instructor earnings summary"""
    if getattr(request.user, 'role', None) != User.UserRole.INSTRUCTOR:
        return Response(
            {'error': 'Only instructors can view earnings'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    revenues = Revenue.objects.filter(instructor=request.user)
    
    summary = {
        'total_revenue': revenues.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0,
        'total_earnings': revenues.aggregate(Sum('instructor_earnings'))['instructor_earnings__sum'] or 0,
        'platform_commission': revenues.aggregate(Sum('platform_commission'))['platform_commission__sum'] or 0,
        'paid_earnings': revenues.filter(is_paid=True).aggregate(Sum('instructor_earnings'))['instructor_earnings__sum'] or 0,
        'pending_earnings': revenues.filter(is_paid=False).aggregate(Sum('instructor_earnings'))['instructor_earnings__sum'] or 0,
        'total_sales': revenues.count(),
        'this_month_earnings': revenues.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).aggregate(Sum('instructor_earnings'))['instructor_earnings__sum'] or 0
    }
    
    return Response(summary)


# Admin Views

class AdminOrderListView(generics.ListAPIView):
    """Admin view of all orders"""
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) != User.UserRole.ADMIN:
            return Order.objects.none()
        
        return Order.objects.all().select_related('user').prefetch_related('items')


class AdminRefundListView(generics.ListAPIView):
    """Admin view of all refunds"""
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Refund.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) != User.UserRole.ADMIN:
            return Refund.objects.none()
        
        return Refund.objects.all().select_related(
            'order', 'requested_by', 'processed_by'
        ).order_by('-created_at')


class CouponListCreateView(generics.ListCreateAPIView):
    """List and create coupons"""
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Coupon.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) == User.UserRole.ADMIN:
            return Coupon.objects.all().order_by('-created_at')
        elif getattr(self.request.user, 'role', None) == User.UserRole.INSTRUCTOR:
            return Coupon.objects.filter(
                created_by=self.request.user
            ).order_by('-created_at')
        else:
            return Coupon.objects.filter(
                is_public=True,
                status=Coupon.CouponStatus.ACTIVE
            ).order_by('-created_at')
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return CouponCreateSerializer
        return CouponSerializer


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Coupon detail management"""
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Coupon.objects.all()
    
    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) == User.UserRole.ADMIN:
            return Coupon.objects.all()
        elif getattr(self.request.user, 'role', None) == User.UserRole.INSTRUCTOR:
            return Coupon.objects.filter(created_by=self.request.user)
        else:
            return Coupon.objects.filter(
                is_public=True,
                status=Coupon.CouponStatus.ACTIVE
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_analytics(request):
    """Payment analytics for admin"""
    if getattr(request.user, 'role', None) != User.UserRole.ADMIN:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Calculate analytics
    orders = Order.objects.filter(status=Order.OrderStatus.COMPLETED)
    payments = Payment.objects.filter(status=Payment.PaymentStatus.COMPLETED)
    
    analytics = {
        'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'total_orders': orders.count(),
        'total_payments': payments.count(),
        'average_order_value': orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
        'this_month_revenue': orders.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'refund_requests': Refund.objects.count(),
        'pending_payouts': InstructorPayout.objects.filter(
            status=InstructorPayout.PayoutStatus.PENDING
        ).count(),
        'active_coupons': Coupon.objects.filter(
            status=Coupon.CouponStatus.ACTIVE
        ).count()
    }
    
    return Response(analytics)


@extend_schema(
    tags=['Financial Management'],
    summary='Admin Revenue Report',
    description='''
    Generate detailed revenue reports for administrators with:
    - Revenue by course/category
    - Revenue by instructor
    - Revenue by time period
    - Export options (CSV, JSON)
    
    **Report Types:**
    - revenue: Platform revenue breakdown
    - payouts: Instructor payout summary
    - refunds: Refund analysis
    - courses: Course performance report
    
    **Export Formats:**
    - JSON (default)
    - CSV
    ''',
    parameters=[
        OpenApiParameter(
            name='report_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Type of report to generate',
            enum=['revenue', 'payouts', 'refunds', 'courses'],
            default='revenue'
        ),
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period for report',
            enum=['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
            default='monthly'
        ),
        OpenApiParameter(
            name='start_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Start date for custom range (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='end_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='End date for custom range (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='format',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Export format',
            enum=['json', 'csv'],
            default='json'
        ),
    ],
    responses={
        200: {
            'description': 'Revenue report generated successfully',
            'content': {
                'application/json': {
                    'example': {
                        'report_id': 'REP20240115ABC123',
                        'report_type': 'revenue',
                        'period': 'monthly',
                        'generated_at': '2024-01-15T10:30:00Z',
                        'data': [
                            {
                                'date': '2024-01-01',
                                'revenue': '5000000.00',
                                'orders': 50,
                                'courses': 5
                            }
                        ]
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_revenue_report(request):
    """Generate detailed revenue reports for administrators"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get parameters
    report_type = request.query_params.get('report_type', 'revenue')
    period = request.query_params.get('period', 'monthly')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    export_format = request.query_params.get('format', 'json')
    
    # Generate report based on type
    if report_type == 'revenue':
        report_data = generate_revenue_report(period, start_date, end_date)
    elif report_type == 'payouts':
        report_data = generate_payout_report(period, start_date, end_date)
    elif report_type == 'refunds':
        report_data = generate_refund_report(period, start_date, end_date)
    elif report_type == 'courses':
        report_data = generate_course_performance_report(period, start_date, end_date)
    else:
        return Response(
            {'error': 'Invalid report type'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Return report
    response_data = {
        'report_id': f"REP{timezone.now().strftime('%Y%m%d')}{timezone.now().microsecond}",
        'report_type': report_type,
        'period': period,
        'generated_at': timezone.now(),
        'data': report_data
    }
    
    if export_format == 'csv':
        # For CSV export, we would typically return a file
        # This is a simplified version - in practice you'd generate a CSV file
        return Response({
            **response_data,
            'message': 'CSV export would be available at download_url in a real implementation'
        })
    
    return Response(response_data)


def generate_revenue_report(period: str, start_date: str | None = None, end_date: str | None = None):
    """Generate revenue report data"""
    # This is a simplified implementation
    # In a real application, you would implement detailed reporting logic
    return [
        {
            'date': '2024-01-01',
            'revenue': '5000000.00',
            'orders': 50,
            'courses': 5
        }
    ]


def generate_payout_report(period: str, start_date: str | None = None, end_date: str | None = None):
    """Generate payout report data"""
    # This is a simplified implementation
    return [
        {
            'period': '2023-12-01 to 2023-12-31',
            'total_payouts': '15000000.00',
            'instructors_paid': 15,
            'completed_payouts': 15
        }
    ]


def generate_refund_report(period: str, start_date: str | None = None, end_date: str | None = None):
    """Generate refund report data"""
    # This is a simplified implementation
    return [
        {
            'period': '2024-01-01 to 2024-01-31',
            'total_refunds': '800000.00',
            'refund_count': 8,
            'refund_rate': '5.33%'
        }
    ]


def generate_course_performance_report(period: str, start_date: str | None = None, end_date: str | None = None):
    """Generate course performance report data"""
    # This is a simplified implementation
    return [
        {
            'course_id': 1,
            'title': 'Python untuk Pemula',
            'revenue': '2500000.00',
            'enrollments': 25,
            'instructor': 'Dr. Jane Smith'
        }
    ]


@extend_schema(
    tags=['Financial Management'],
    summary='Process Instructor Payout',
    description='''
    Process instructor payouts manually by administrators.
    
    **Required Fields:**
    - instructor_id: ID of instructor to payout
    - period_start: Start date of payout period
    - period_end: End date of payout period
    - amount: Payout amount
    - payout_method: Method of payout (bank_transfer, paypal, etc.)
    - notes: Optional notes about the payout
    
    **Process:**
    1. Validate instructor and period
    2. Calculate earnings for period
    3. Create payout record
    4. Update revenue records
    5. Notify instructor
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'instructor_id': {
                    'type': 'integer',
                    'description': 'ID of instructor to payout'
                },
                'period_start': {
                    'type': 'string',
                    'format': 'date',
                    'description': 'Start date of payout period (YYYY-MM-DD)'
                },
                'period_end': {
                    'type': 'string',
                    'format': 'date',
                    'description': 'End date of payout period (YYYY-MM-DD)'
                },
                'amount': {
                    'type': 'number',
                    'format': 'decimal',
                    'description': 'Payout amount'
                },
                'payout_method': {
                    'type': 'string',
                    'description': 'Method of payout'
                },
                'notes': {
                    'type': 'string',
                    'description': 'Optional notes'
                }
            },
            'required': ['instructor_id', 'period_start', 'period_end', 'amount', 'payout_method']
        }
    },
    responses={
        201: {
            'description': 'Payout processed successfully',
            'content': {
                'application/json': {
                    'example': {
                        'payout_id': 'PO20240115ABC123',
                        'message': 'Payout processed successfully',
                        'amount': '2250000.00',
                        'instructor': 'Dr. Jane Smith'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Invalid data',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Invalid instructor or period'
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_instructor_payout(request):
    """Process instructor payouts manually"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get request data
    instructor_id = request.data.get('instructor_id')
    period_start = request.data.get('period_start')
    period_end = request.data.get('period_end')
    amount = request.data.get('amount')
    payout_method = request.data.get('payout_method')
    notes = request.data.get('notes', '')
    
    # Validate required fields
    if not all([instructor_id, period_start, period_end, amount, payout_method]):
        return Response(
            {'error': 'Missing required fields'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate instructor
    try:
        instructor = User.objects.get(id=instructor_id, role=User.UserRole.INSTRUCTOR)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid instructor'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create payout record
    payout = InstructorPayout.objects.create(
        instructor=instructor,
        period_start=period_start,
        period_end=period_end,
        gross_revenue=amount,
        platform_commission=Decimal('0.00'),  # Assuming admin sets net amount directly
        commission_rate=Decimal('0.0000'),
        net_amount=amount,
        payout_method=payout_method,
        payout_details={},
        status=InstructorPayout.PayoutStatus.PROCESSING,
        processed_by=request.user,
        notes=notes
    )
    
    # Update revenue records to mark as paid
    Revenue.objects.filter(
        instructor=instructor,
        created_at__gte=period_start,
        created_at__lte=period_end,
        is_paid=False
    ).update(
        is_paid=True,
        payout=payout,
        paid_at=timezone.now()
    )
    
    # Update payout status to completed
    payout.status = InstructorPayout.PayoutStatus.COMPLETED
    payout.processed_at = timezone.now()
    payout.save()
    
    return Response({
        'payout_id': payout.payout_id,
        'message': 'Payout processed successfully',
        'amount': payout.net_amount,
        'instructor': instructor.full_name or instructor.username
    }, status=status.HTTP_201_CREATED)
