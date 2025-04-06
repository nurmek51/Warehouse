from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import pandas as pd
from .models import Upload
from store.models import StoreItem
from .serializers import UploadSerializer
from store.serializers import StoreItemSerializer
import logging
logger = logging.getLogger(__name__)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        file_path = default_storage.save(file_obj.name, file_obj)
        file_name = file_obj.name.lower().strip()
        try:
            if file_name.endswith('.csv'):
                df = pd.read_csv(default_storage.path(file_path), encoding='utf-8-sig')
            elif file_name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(default_storage.path(file_path))
            else:
                return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if 'barcode' in df.columns:
            df = df.drop(columns=['barcode'])

        upload = Upload.objects.create(file_name=file_obj.name, uploaded_by=request.user)
        if request.user.role != 'manager':
            request.user.role = 'manager'
            request.user.save()
        count = 0
        for index, row in df.iterrows():
            try:
                name = row.get('name')
                category = row.get('category')
                quantity = int(row.get('quantity'))
                price_val = row.get('price')
                price = float(price_val) if price_val is not None else None
                expire_date_str = row.get('expire_date')
                expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').date() if expire_date_str else None
                StoreItem.objects.create(
                    name=name,
                    category=category,
                    quantity=quantity,
                    price=price,
                    expire_date=expire_date,
                    status='warehouse',
                    barcode=None,
                    warehouse_upload=upload
                )
                count += 1
            except Exception as e:
                logger.error("Ошибка при импорте строки %s: %s", index, e)
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
        items = StoreItem.objects.filter(warehouse_upload_id=file_id, status='warehouse')
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

class TransferToStoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('productId')
        transfer_quantity = request.data.get('quantity')
        if not product_id or not transfer_quantity:
            return Response({"error": "productId and quantity are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transfer_quantity = int(transfer_quantity)
            product = StoreItem.objects.get(id=product_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        if product.status != 'warehouse':
            return Response({"error": "Product is not on warehouse"}, status=status.HTTP_400_BAD_REQUEST)

        if product.quantity < transfer_quantity:
            return Response({"error": "Insufficient quantity on warehouse"}, status=status.HTTP_400_BAD_REQUEST)

        if product.quantity == transfer_quantity:
            product.status = 'showcase'
            product.save()
            return Response({"message": "Product moved to showcase"}, status=status.HTTP_200_OK)
        else:
            product.quantity -= transfer_quantity
            product.save()
            new_product = StoreItem.objects.create(
                name=product.name,
                category=product.category,
                quantity=transfer_quantity,
                price=product.price,
                expire_date=product.expire_date,
                status='showcase',
                barcode=product.barcode,
                warehouse_upload=product.warehouse_upload
            )
            serializer = StoreItemSerializer(new_product)
            return Response({"message": "Product transferred to showcase", "store_item": serializer.data},
                            status=status.HTTP_200_OK)


class ExpiringItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threshold_days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        threshold_date = today + timedelta(days=threshold_days)
        items = StoreItem.objects.filter(expire_date__lte=threshold_date)
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)