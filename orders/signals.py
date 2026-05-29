from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order, DeliveryCode
from .tasks import send_order_status_email_task, send_delivery_code_email_task


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """Track if order status has changed before saving."""
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            instance._status_changed = old_order.status != instance.status
            instance._old_status = old_order.status
        except Order.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = False


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Send email notification when order status changes.
    Generate delivery code when status changes to OUT_FOR_DELIVERY.
    """
    if created:
        # Don't send status email on creation (confirmation email sent separately)
        return
    
    # Only send email if status actually changed
    if hasattr(instance, '_status_changed') and instance._status_changed:
        # Send status update email asynchronously
        try:
            send_order_status_email_task.delay(instance.id)
            print(f"✉️  Status update email queued for {instance.order_number}: {instance._old_status} → {instance.status}")
        except Exception as e:
            print(f"❌ Failed to queue status email for {instance.order_number}: {e}")
        
        # Generate delivery code if status changed to OUT_FOR_DELIVERY
        if instance.status == 'OUT_FOR_DELIVERY':
            # Check if delivery code already exists
            if not hasattr(instance, 'delivery_code'):
                delivery_code = DeliveryCode.objects.create(
                    order=instance,
                    code=DeliveryCode.generate_code()
                )
                
                # Send delivery code email asynchronously
                try:
                    send_delivery_code_email_task.delay(instance.id, delivery_code.code)
                    print(f"🔑 Delivery code email queued for {instance.order_number}: {delivery_code.code}")
                except Exception as e:
                    print(f"❌ Failed to queue delivery code email for {instance.order_number}: {e}")


