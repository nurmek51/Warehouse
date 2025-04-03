from django.urls import path
from django.views import View

urlpatterns = [
    path('', View.as_view(), name=''),
]
