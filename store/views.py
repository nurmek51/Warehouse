from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import StoreItem
from .serializers import StoreItemSerializer
from accounts.permissions import IsManager

class StoreItemListView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        items = StoreItem.objects.filter(status="showcase")
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

class DiscountView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

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
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if item.status != "витрине":
            return Response(
                {"error": "Discount can only be applied to items on display (витрине)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if item.price is None:
            return Response(
                {"error": "Item price is not set"},
                status=status.HTTP_400_BAD_REQUEST
            )
        item.price = item.price * (1 - float(discount_percentage) / 100)
        item.save()
        return Response(
            {"message": "Discount applied"},
            status=status.HTTP_200_OK
        )

class RemoveExpiredView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

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

    def post(self, request):
        product_id = request.data.get('productId')
        transfer_quantity = request.data.get('quantity')
        if not product_id or not transfer_quantity:
            return Response(
                {"error": "productId and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            transfer_quantity = int(transfer_quantity)
            product = StoreItem.objects.get(id=product_id)
        except StoreItem.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid quantity"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.status != 'showcase':
            return Response(
                {"error": "Product is not on store"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.quantity < transfer_quantity:
            return Response(
                {"error": "Insufficient quantity on store"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.quantity == transfer_quantity:
            product.status = 'warehouse'
            product.save()
            return Response(
                {"message": "Product transferred to warehouse"},
                status=status.HTTP_200_OK
            )
        else:
            product.quantity -= transfer_quantity
            product.save()
            new_product = StoreItem.objects.create(
                name=product.name,
                category=product.category,
                quantity=transfer_quantity,
                price=product.price,
                expire_date=product.expire_date,
                status='warehouse',
                barcode=product.barcode,
                warehouse_upload=product.warehouse_upload
            )
            serializer = StoreItemSerializer(new_product)
            return Response(
                {"message": "Product transferred to warehouse", "warehouse_item": serializer.data},
                status=status.HTTP_200_OK
            )

class SellStoreItemView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request):
        product_id = request.data.get('productId')
        sell_quantity = request.data.get('quantity', 1)
        if not product_id:
            return Response({"error": "productId is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            sell_quantity = int(sell_quantity)
            product = StoreItem.objects.get(id=product_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        if product.status != 'showcase':
            return Response({"error": "Product is not on store"}, status=status.HTTP_400_BAD_REQUEST)

        if product.quantity < sell_quantity:
            return Response({"error": "Insufficient quantity on store"}, status=status.HTTP_400_BAD_REQUEST)

        product.quantity -= sell_quantity
        if product.quantity == 0:
            product.status = 'deleted'
        product.save()
        return Response({"message": "Product sold"}, status=status.HTTP_200_OK)


class ScanBarcodeView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request, barcode):
        try:
            product = StoreItem.objects.get(barcode=barcode)
        except StoreItem.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "name": product.name,
            "category": product.category,
            "quantity": product.quantity,
            "price": str(product.price) if product.price is not None else None,
            "expire_date": product.expire_date,
            "status": product.status,
            "is_expired": product.is_expired,
            "barcode": product.barcode,
        }

        if product.status == 'warehouse':
            data["message"] = "Item on warehouse at the moment."
        elif product.status == 'showcase':
            data["message"] = "All data about product. Can sell."
        elif product.status == 'sold':
            data["message"] = "Product sold"
        elif product.status == 'deleted':
            data["message"] = "Product deleted"

        return Response(data, status=status.HTTP_200_OK)