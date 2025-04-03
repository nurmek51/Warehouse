from django.db import models

# Create your models here.

class StoreItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expire_date = models.DateField()
    status = models.CharField(max_length=50, default='active')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name