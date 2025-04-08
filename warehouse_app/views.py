from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import datetime, date, timedelta
import unicodedata
from dateutil import parser as date_parser
import pandas as pd
from .models import Upload
from store.models import StoreItem
from .serializers import UploadSerializer, UploadFileSerializer
from store.serializers import StoreItemSerializer
import logging
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import re

logger = logging.getLogger(__name__)
DASH_RE = re.compile(r"[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D]")

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Warehouse"],
        operation_summary="Импорт товаров на склад",
        request_body=UploadFileSerializer,
        responses={
            201: openapi.Response("Количество импортированных строк"),
            400: "Ошибка валидации / формата файла",
        },
    )
    def post(self, request):
        def to_date(value) -> date | None:
            """
            Универсальный парсер даты:
            • Timestamp / datetime / date
            • Excel‑serial (число)
            • Строки с любыми тире, слешами, точками: 2025‑04‑09, 09‑04‑2025, 4/9/25, 09.04.2025
            """
            if pd.isna(value):
                return None

            if isinstance(value, (pd.Timestamp, datetime)):
                return value.date()
            if isinstance(value, date):
                return value

            # Excel serial
            if isinstance(value, (int, float)):
                try:
                    return (date(1899, 12, 30) + timedelta(days=int(value))).date()
                except Exception:
                    pass

            cleaned = str(value).strip()
            cleaned = unicodedata.normalize("NFKD", cleaned)
            cleaned = DASH_RE.sub("-", cleaned)

            known = [
                "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
                "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
                "%d.%m.%Y", "%Y.%m.%d",
            ]
            for fmt in known:
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    continue

            try:
                return date_parser.parse(cleaned, fuzzy=True, dayfirst=False).date()
            except (ValueError, OverflowError):
                raise ValueError(f"Unrecognised date format: {value!r}")

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = default_storage.save(file_obj.name, file_obj)
        try:
            if file_obj.name.lower().endswith(".csv"):
                df = pd.read_csv(default_storage.path(file_path), encoding="utf-8-sig")
            elif file_obj.name.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(default_storage.path(file_path))
            else:
                return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        df = df.drop(columns=[c for c in ("barcode",) if c in df.columns])

        upload = Upload.objects.create(file_name=file_obj.name, uploaded_by=request.user)
        if request.user.role != "manager":
            request.user.role = "manager"
            request.user.save()

        imported = 0
        for idx, row in df.iterrows():
            try:
                StoreItem.objects.create(
                    name=row.get("name"),
                    category=row.get("category"),
                    quantity=int(row.get("quantity")),
                    price=float(row["price"]) if pd.notna(row.get("price")) else None,
                    expire_date=to_date(row.get("expire_date")),
                    status="warehouse",
                    barcode=None,
                    warehouse_upload=upload,
                )
                imported += 1
            except Exception as exc:
                logger.error("Ошибка при импорте строки %s: %s", idx, exc)
                continue

        return Response({"imported": imported}, status=status.HTTP_201_CREATED)


class UploadListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Warehouse"],
        operation_summary="Список загруженных файлов",
    )
    def get(self, request):
        uploads = Upload.objects.all()
        serializer = UploadSerializer(uploads, many=True)
        return Response(serializer.data)


class WarehouseItemsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Warehouse"],
        operation_summary="Товары конкретного файла",
        responses={200: StoreItemSerializer(many=True)},
    )
    def get(self, request, file_id):
        items = StoreItem.objects.filter(warehouse_upload_id=file_id, status='warehouse')
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

class TransferToStoreView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Warehouse"],
        operation_summary="Переместить со склада в витрину",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["productId", "quantity"],
            properties={
                "productId": openapi.Schema(type=openapi.TYPE_INTEGER),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            200: openapi.Response(
                description="Товар, оказавшийся на витрине",
                schema=StoreItemSerializer(),
            ),
            400: "Validation error / Business rule violated",
            404: "Product not found",
        },
    )
    def post(self, request):
        product_id = request.data.get("productId")
        transfer_quantity = request.data.get("quantity")

        if not product_id or transfer_quantity is None:
            return Response(
                {"error": "productId and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transfer_quantity = int(transfer_quantity)
            product = StoreItem.objects.get(id=product_id)
        except StoreItem.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST
            )

        if product.status != "warehouse":
            return Response(
                {"error": "Product is not on warehouse"}, status=status.HTTP_400_BAD_REQUEST
            )

        if product.quantity < transfer_quantity:
            return Response(
                {"error": "Insufficient quantity on warehouse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if product.quantity == transfer_quantity:
            product.status = "showcase"
            product.save()
            target_item = product
        else:
            product.quantity -= transfer_quantity
            product.save()
            target_item = StoreItem.objects.create(
                name=product.name,
                category=product.category,
                quantity=transfer_quantity,
                price=product.price,
                expire_date=product.expire_date,
                status="showcase",
                barcode=product.barcode,
                warehouse_upload=product.warehouse_upload,
            )

        serializer = StoreItemSerializer(target_item)
        return Response(
            {
                "message": "Product transferred to showcase",
                "store_item": serializer.data,
            },
            status=status.HTTP_200_OK,
        )



class ExpiringItemsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Warehouse"],
        operation_summary="Скоро истекающие товары",
        manual_parameters=[openapi.Parameter(
            name="days",
            in_=openapi.IN_QUERY,
            description="Горизонт в днях (по умолчанию 7)",
            type=openapi.TYPE_INTEGER,
        )],
    )
    def get(self, request):
        threshold_days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        threshold_date = today + timedelta(days=threshold_days)
        items = StoreItem.objects.filter(expire_date__lte=threshold_date)
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)