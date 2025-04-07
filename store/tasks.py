from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from store.models import StoreItem

@shared_task
def send_expiry_notifications():
    today = timezone.now().date()
    notified_count = 0
    expired_count = 0
    products = StoreItem.objects.filter(status__in=['warehouse', 'showcase'])
    for product in products:
        full_lifetime = (product.expire_date - product.added_at.date()).days
        if full_lifetime <= 0:
            continue
        remaining_days = (product.expire_date - today).days
        if remaining_days <= 0:
            if product.warehouse_upload and product.warehouse_upload.uploaded_by:
                recipient = product.warehouse_upload.uploaded_by.email
                send_mail(
                    subject=f"Product Expired: {product.name}",
                    message=(
                        f"Dear user,\n\nThe product '{product.name}' expired on {product.expire_date}.\n"
                        "Please take necessary actions."
                    ),
                    from_email='nurmeksdu@gmail.com',
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                expired_count += 1
        elif (remaining_days / full_lifetime) <= 0.3:
            if product.warehouse_upload and product.warehouse_upload.uploaded_by:
                recipient = product.warehouse_upload.uploaded_by.email
                send_mail(
                    subject=f"Expiry Warning for {product.name}",
                    message=(
                        f"Dear user,\n\nThe product '{product.name}' is nearing its expiration date ({product.expire_date}). "
                        f"It has only {remaining_days} days left, which is less than 30% of its total shelf life.\n\n"
                        "Please take necessary actions."
                    ),
                    from_email='maxsatul2007@gmail.com',
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                notified_count += 1
    return f"Expiry notifications sent for {notified_count} products; Expiry alerts sent for {expired_count} expired products."
