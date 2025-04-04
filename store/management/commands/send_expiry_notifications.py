from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from store.models import StoreItem
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send notifications for products nearing expiration'

    def handle(self, *args, **options):
        threshold_days = 7
        today = timezone.now().date()
        threshold_date = today + timedelta(days=threshold_days)

        products = StoreItem.objects.filter(expire_date__lte=threshold_date).exclude(status='sold')
        for product in products:
            if product.warehouse_upload and product.warehouse_upload.uploaded_by:
                recipient = product.warehouse_upload.uploaded_by.email
                subject = f"Notification: expiration date of the product '{product.name}' expires {product.expire_date}"
                message = (
                    f"Dear User,\n\n"
                    f"Please note that the expiration date of the product '{product.name}' (category: {product.category}) "
                    f"expires {product.expire_date}. It is recommended to take the necessary actions.\n\n"
                    "With respect,\nYour warehouse management system"
                )
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
                    self.stdout.write(f"Notification sent for product {product.name} to {recipient}")
                except Exception as e:
                    self.stdout.write(f"Failed to send notification for {product.name}: {e}")
        self.stdout.write("Notifications sent.")
