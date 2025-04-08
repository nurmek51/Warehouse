from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import StoreItem
from .serializers import StoreItemSerializer
from accounts.permissions import IsManager
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

class StoreItemListView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Все товары на витрине",
    )
    def get(self, request):
        items = StoreItem.objects.filter(status="showcase")
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

class DiscountView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Применить скидку",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["storeItemId", "discountPercentage"],
            properties={
                "storeItemId": openapi.Schema(type=openapi.TYPE_INTEGER),
                "discountPercentage": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
    )
    def post(self, request):
        store_item_id = request.data.get('storeItemId')
        discount_percentage = request.data.get('discountPercentage')

        if not store_item_id or discount_percentage is None:
            return Response(
                {"error": "storeItemId and discountPercentage are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = StoreItem.objects.get(id=store_item_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        if item.status != "showcase":
            return Response(
                {"error": "Discount can only be applied to items on showcase."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if item.price is None:
            return Response({"error": "Item price is not set"}, status=status.HTTP_400_BAD_REQUEST)

        old_price = item.price
        try:
            discount_decimal = Decimal(discount_percentage)
        except Exception:
            return Response({"error": "Invalid discountPercentage"}, status=status.HTTP_400_BAD_REQUEST)

        new_price = old_price * (Decimal('1') - discount_decimal / Decimal('100'))
        item.price = new_price
        item.save()

        return Response(
            {
                "message": "Discount applied",
                "old_price": str(old_price),
                "new_price": str(new_price)
            },
            status=status.HTTP_200_OK
        )

class RemoveExpiredView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Удалить просроченный товар",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["productId"],
            properties={"productId": openapi.Schema(type=openapi.TYPE_INTEGER)},
        )
    )
    def post(self, request):
        product_id = request.data.get('productId')
        if not product_id:
            return Response({"error": "productId is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = StoreItem.objects.get(id=product_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        if not product.is_expired:
            return Response({"error": "Product is not expired"}, status=status.HTTP_400_BAD_REQUEST)

        product.status = 'deleted'
        product.save()
        return Response({"message": "Product deleted (moved to trash)"}, status=status.HTTP_200_OK)


class TransferToWarehouseView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Вернуть товар со витрины на склад",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["productId", "quantity"],
            properties={
                "productId": openapi.Schema(type=openapi.TYPE_INTEGER),
                "quantity":  openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            200: openapi.Response(
                description="Складская позиция после перемещения",
                schema=StoreItemSerializer(),
            ),
            400: "Validation error / Business rule violated",
            404: "Product not found",
        },
    )
    def post(self, request):
        product_id        = request.data.get("productId")
        transfer_quantity = request.data.get("quantity")

        if not product_id or transfer_quantity is None:
            return Response({"error": "productId and quantity are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            transfer_quantity = int(transfer_quantity)
            product = StoreItem.objects.get(id=product_id)
        except (StoreItem.DoesNotExist, ValueError):
            return Response({"error": "Invalid productId or quantity"},
                            status=status.HTTP_400_BAD_REQUEST)

        if product.status != "showcase":
            return Response({"error": "Product is not on store"},
                            status=status.HTTP_400_BAD_REQUEST)

        if product.quantity < transfer_quantity:
            return Response({"error": "Insufficient quantity on store"},
                            status=status.HTTP_400_BAD_REQUEST)

        if product.quantity == transfer_quantity:
            product.status = "warehouse"
            product.save()
            target_item = product
        else:
            product.quantity -= transfer_quantity
            product.save()

            target_item, _ = StoreItem.objects.get_or_create(
                barcode=product.barcode,
                status="warehouse",
                defaults={
                    "name":      product.name,
                    "category":  product.category,
                    "quantity":  0,
                    "price":     product.price,
                    "expire_date": product.expire_date,
                    "warehouse_upload": product.warehouse_upload,
                },
            )
            target_item.quantity += transfer_quantity
            target_item.save()

        serializer = StoreItemSerializer(target_item)
        return Response(
            {
                "message": "Product transferred to warehouse",
                "warehouse_item": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class SellStoreItemView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Продать товар",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["productId"],
            properties={
                "productId": openapi.Schema(type=openapi.TYPE_INTEGER),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, default=1),
            },
        )

    )
    def post(self, request):
        product_id     = request.data.get("productId")
        sell_quantity  = request.data.get("quantity", 1)
        if not product_id:
            return Response({"error": "productId is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            sell_quantity = int(sell_quantity)
            product = StoreItem.objects.get(id=product_id)
        except (StoreItem.DoesNotExist, ValueError):
            return Response({"error": "Invalid productId or quantity"},
                            status=status.HTTP_400_BAD_REQUEST)

        if product.status != "showcase":
            return Response({"error": "Product is not on store"},
                            status=status.HTTP_400_BAD_REQUEST)
        if product.quantity < sell_quantity:
            return Response({"error": "Insufficient quantity on store"},
                            status=status.HTTP_400_BAD_REQUEST)

        product.quantity -= sell_quantity
        if product.quantity == 0:
            product.status = "deleted"
        product.save()

        # создаём / увеличиваем sold‑запись
        sold_item, _ = StoreItem.objects.get_or_create(
            barcode=product.barcode,
            status="sold",
            defaults={
                "name":      product.name,
                "category":  product.category,
                "quantity":  0,
                "price":     product.price,
                "expire_date": product.expire_date,
                "added_at":  timezone.now(),
            },
        )
        sold_item.quantity += sell_quantity
        sold_item.save()

        return Response({"message": "Product sold"}, status=status.HTTP_200_OK)

class ScanBarcodeView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        tags=["Store"],
        operation_summary="Поиск товара по штрих‑коду",
        responses={200: "Информация о товаре", 404: "Not found"},
    )
    def get(self, request, barcode):
        try:
            product = (
                StoreItem.objects
                .filter(barcode=barcode, status="showcase")
                .first()
            )
            if not product:
                raise StoreItem.DoesNotExist
        except StoreItem.DoesNotExist:
            return Response({"error": "Product not found on showcase"},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = StoreItemSerializer(product)
        data = serializer.data
        data["message"] = "All data about product. Can sell."

        return Response(data, status=status.HTTP_200_OK)