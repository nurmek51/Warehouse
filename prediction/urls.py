from django.urls import path
from .views import ForecastResultView

urlpatterns = [
    path('result', ForecastResultView.as_view(), name='forecast-result'),
]
