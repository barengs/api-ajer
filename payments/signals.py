from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, InstructorPayout

# Optional import for notifications
try:
    from notifications.models import Notification  # type: ignore
except ImportError:
    Notification = None


@receiver(post_save, sender=Order)
def handle_order_completion(sender, instance, created, **kwargs):
    """Handle actions when an order is completed"""
    if not created and instance.status == 'completed':
        # Notify student about successful purchase
        if Notification is not None:
            Notification.objects.create(
                user=instance.user,
                title="Purchase Successful",
                message=f"Your order #{instance.id} has been completed successfully.",
                notification_type="payment"
            )
        
        # Create enrollments for purchased courses
        for item in instance.items.all():
            from courses.models import Enrollment
            Enrollment.objects.get_or_create(
                student=instance.user,
                course=item.course,
                defaults={
                    'amount_paid': item.price
                }
            )


@receiver(post_save, sender=InstructorPayout)
def handle_instructor_payout(sender, instance, created, **kwargs):
    """Handle actions when instructor payout is processed"""
    if created:
        # Notify instructor about payout
        if Notification is not None:
            Notification.objects.create(
                user=instance.instructor,
                title="Payout Processed",
                message=f"Your payout of ${instance.amount} has been processed.",
                notification_type="payout"
            )