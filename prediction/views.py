from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from prediction.forecast_tasks import forecast_by_category

class ForecastResultView(APIView):
    def get(self, request):
        result = forecast_by_category.apply()
        return Response(result.result, status=status.HTTP_200_OK)
