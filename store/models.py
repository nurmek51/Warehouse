from django.db import models
from django.utils import timezone
import random

# Create your models here.

class StoreItem(models.Model):
    STATUS_CHOICES = [
        ('warehouse', 'On warehouse'),
        ('showcase', 'On showcase'),
        ('sold', 'Sold'),
        ('deleted', 'Deleted'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='warehouse')
    is_expired = models.BooleanField(default=False)
    barcode = models.CharField(max_length=255, blank=True, null=True, unique=False)
    added_at = models.DateTimeField(auto_now_add=True)
    warehouse_upload = models.ForeignKey('warehouse_app.Upload', on_delete=models.SET_NULL, null=True, blank=True)

    def generate_unique_barcode(self):
        while True:
            code = str(random.randint(10**11, 10**12 - 1))
            if code not in StoreItem.objects.all():
                if not StoreItem.objects.filter(barcode=code).exists():
                    return code
            else:
                self.generate_unique_barcode()

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_unique_barcode()
        if self.expire_date < timezone.now().date():
            self.is_expired = True
        else:
            self.is_expired = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name