from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import timedelta
import pandas as pd

from .models import Upload, WarehouseItem
from .serializers import UploadSerializer, WarehouseItemSerializer


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = default_storage.save(file_obj.name, file_obj)
        try:
            if file_obj.name.endswith('.csv'):
                df = pd.read_csv(default_storage.path(file_path))
            elif file_obj.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(default_storage.path(file_path))
            else:
                return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        upload = Upload.objects.create(file_name=file_obj.name, uploaded_by=request.user)
        count = 0
        for _, row in df.iterrows():
            try:
                WarehouseItem.objects.create(
                    upload=upload,
                    name=row.get('name'),
                    category=row.get('category'),
                    quantity=row.get('quantity'),
                    expire_date=row.get('expire_date'),
                    cost=row.get('cost'),
                )
                count += 1
            except Exception as e:
                continue
        return Response({"imported": count}, status=status.HTTP_201_CREATED)


class UploadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uploads = Upload.objects.all()
        serializer = UploadSerializer(uploads, many=True)
        return Response(serializer.data)


class WarehouseItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        items = WarehouseItem.objects.filter(upload_id=file_id)
        serializer = WarehouseItemSerializer(items, many=True)
        return Response(serializer.data)


class TransferToStoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('itemId')
        quantity = request.data.get('quantity')
        if not item_id or not quantity:
            return Response({"error": "itemId and quantity are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = WarehouseItem.objects.get(id=item_id)
        except WarehouseItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        if item.quantity < int(quantity):
            return Response({"error": "Insufficient quantity"}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity -= int(quantity)
        item.save()
        return Response({"message": "Item moved to store"}, status=status.HTTP_200_OK)


class ExpiringItemsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        threshold_days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        threshold_date = today + timedelta(days=threshold_days)
        items = WarehouseItem.objects.filter(expire_date__lte=threshold_date)
        serializer = WarehouseItemSerializer(items, many=True)
        return Response(serializer.data)
