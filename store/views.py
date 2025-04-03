from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import StoreItem
from .serializers import StoreItemSerializer

class StoreItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = StoreItem.objects.filter(status="active")
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

class DiscountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        store_item_id = request.data.get('storeItemId')
        discount_percentage = request.data.get('discountPercentage')
        if not store_item_id or discount_percentage is None:
            return Response({"error": "storeItemId and discountPercentage are required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            item = StoreItem.objects.get(id=store_item_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        item.price = item.price * (1 - float(discount_percentage) / 100)
        item.save()
        return Response({"message": "Discount applied"}, status=status.HTTP_200_OK)

class RemoveExpiredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        store_item_id = request.data.get('storeItemId')
        if not store_item_id:
            return Response({"error": "storeItemId is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = StoreItem.objects.get(id=store_item_id)
        except StoreItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        item.status = 'removed'
        item.save()
        return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
