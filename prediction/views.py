from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class PredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        return Response({
            "itemId": item_id,
            "forecast": [],
            "recommendation": "Not implemented yet"
        })

# ETO ZAGLUSHKA