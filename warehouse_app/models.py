from django.db import models
from django.conf import settings

class Upload(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.file_name

class WarehouseItem(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField()
    expire_date = models.DateField()
    cost = models.IntegerField()

    def __str__(self):
        return self.name
