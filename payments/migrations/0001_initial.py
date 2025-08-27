# Generated migration for payments app

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'shopping_carts',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=20, unique=True)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('coupon_code', models.CharField(blank=True, max_length=50)),
                ('coupon_discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending Payment'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('billing_email', models.EmailField(max_length=254)),
                ('billing_name', models.CharField(max_length=200)),
                ('billing_address', models.JSONField(blank=True, default=dict)),
                ('user_agent', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')], max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('minimum_order_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('maximum_discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('usage_limit', models.IntegerField(blank=True, null=True)),
                ('usage_limit_per_user', models.IntegerField(blank=True, null=True)),
                ('current_usage_count', models.IntegerField(default=0)),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_coupons', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'coupons',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='courses.coursebatch')),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='payments.shoppingcart')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='courses.course')),
            ],
            options={
                'db_table': 'cart_items',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('course_title', models.CharField(max_length=200)),
                ('instructor_name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='courses.coursebatch')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='courses.course')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='payments.order')),
            ],
            options={
                'db_table': 'order_items',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.CharField(max_length=50, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('bank_transfer', 'Bank Transfer'), ('e_wallet', 'E-Wallet'), ('virtual_account', 'Virtual Account'), ('paypal', 'PayPal'), ('stripe', 'Stripe')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded'), ('partially_refunded', 'Partially Refunded')], default='pending', max_length=20)),
                ('gateway', models.CharField(blank=True, max_length=50)),
                ('gateway_transaction_id', models.CharField(blank=True, max_length=100)),
                ('gateway_response', models.JSONField(blank=True, default=dict)),
                ('gateway_fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('net_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('failure_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='payments.order')),
            ],
            options={
                'db_table': 'payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('refund_id', models.CharField(max_length=50, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.CharField(choices=[('customer_request', 'Customer Request'), ('order_cancellation', 'Order Cancellation'), ('duplicate_payment', 'Duplicate Payment'), ('fraud_chargeback', 'Fraud/Chargeback'), ('technical_error', 'Technical Error'), ('policy_violation', 'Policy Violation'), ('other', 'Other')], max_length=30)),
                ('reason_description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('gateway_refund_id', models.CharField(blank=True, max_length=100)),
                ('gateway_response', models.JSONField(blank=True, default=dict)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='payments.order')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='payments.payment')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_refunds', to=settings.AUTH_USER_MODEL)),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_refunds', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'refunds',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InstructorPayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payout_id', models.CharField(max_length=50, unique=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('total_revenue', models.DecimalField(decimal_places=2, max_digits=10)),
                ('platform_fee', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payout_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('payment_method', models.CharField(blank=True, max_length=50)),
                ('payment_details', models.JSONField(blank=True, default=dict)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payouts', to=settings.AUTH_USER_MODEL)),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_payouts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'instructor_payouts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InstructorRevenue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gross_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('platform_fee_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('platform_fee_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('instructor_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='revenues', to=settings.AUTH_USER_MODEL)),
                ('order_item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='revenue', to='payments.orderitem')),
                ('payout', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='revenues', to='payments.instructorpayout')),
            ],
            options={
                'db_table': 'instructor_revenues',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='payments.coupon')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_usages', to='payments.order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_usages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'coupon_usages',
                'ordering': ['-used_at'],
            },
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', 'status'], name='orders_user_id_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_number'], name='orders_order_number_b02db0_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['-created_at'], name='orders_created_at_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['order', 'status'], name='payments_order_status_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_id'], name='payments_payment_id_b02db0_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['-created_at'], name='payments_created_at_fd23b8_idx'),
        ),
        migrations.AddIndex(
            model_name='refund',
            index=models.Index(fields=['payment', 'status'], name='refunds_payment_status_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='instructorpayout',
            index=models.Index(fields=['instructor', 'status'], name='payouts_instructor_status_9393e2_idx'),
        ),
        migrations.AddIndex(
            model_name='instructorpayout',
            index=models.Index(fields=['period_start', 'period_end'], name='payouts_period_range_b02db0_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'course', 'batch')},
        ),
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('order', 'course', 'batch')},
        ),
        migrations.AlterUniqueTogether(
            name='couponusage',
            unique_together={('coupon', 'user', 'order')},
        ),
    ]