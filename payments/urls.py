from django.urls import path, include
from . import views

urlpatterns = [
    # Shopping Cart
    path('cart/', views.ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/add/', views.CartItemCreateView.as_view(), name='add_to_cart'),
    path('cart/item/<int:pk>/remove/', views.CartItemDeleteView.as_view(), name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Coupons
    path('coupon/validate/', views.validate_coupon, name='validate_coupon'),
    path('coupons/', views.CouponListCreateView.as_view(), name='coupon_list'),
    path('coupon/<int:pk>/', views.CouponDetailView.as_view(), name='coupon_detail'),
    
    # Orders
    path('order/create/', views.OrderCreateView.as_view(), name='create_order'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Payments
    path('order/<int:order_id>/pay/', views.PaymentCreateView.as_view(), name='process_payment'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    
    # Refunds
    path('payment/<int:payment_id>/refund/', views.RefundRequestView.as_view(), name='request_refund'),
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    
    # Instructor Revenue
    path('instructor/revenue/', views.InstructorRevenueView.as_view(), name='instructor_revenue'),
    path('instructor/payouts/', views.InstructorPayoutListView.as_view(), name='instructor_payouts'),
    path('instructor/earnings/', views.instructor_earnings_summary, name='instructor_earnings'),
    
    # Admin Views
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin_orders'),
    path('admin/refunds/', views.AdminRefundListView.as_view(), name='admin_refunds'),
    path('admin/analytics/', views.payment_analytics, name='payment_analytics'),
    path('admin/reports/', views.admin_revenue_report, name='admin_revenue_report'),
    path('admin/payouts/process/', views.process_instructor_payout, name='process_instructor_payout'),
    
    # Financial Management
    path('financial/', include('payments.financial_urls')),
]