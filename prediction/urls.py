from django.urls import path
from .views import PredictionView

urlpatterns = [
    path('<int:item_id>', PredictionView.as_view(), name='prediction'),
]
