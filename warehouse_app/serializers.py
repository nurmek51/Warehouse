from rest_framework import serializers
from .models import Upload

class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = '__all__'

class UploadFileSerializer(serializers.Serializer):
    file = serializers.FileField(
        required=True,
        help_text="CSV, XLS или XLSX‑файл с товарами"
    )