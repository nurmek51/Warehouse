from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from prediction.forecast_tasks import forecast_by_category
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ForecastResultView(APIView):
    @swagger_auto_schema(
        tags=["Forecast"],
        operation_summary="Получить прогноз продаж",
        responses={200: openapi.Response("JSON‑результат")},
    )
    def get(self, request):
        result = forecast_by_category.apply()
        return Response(result.result, status=status.HTTP_200_OK)
