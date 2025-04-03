from django.urls import path
from .views import StoreItemListView, DiscountView, RemoveExpiredView

urlpatterns = [
    path('items', StoreItemListView.as_view(), name='store-items'),
    path('discount', DiscountView.as_view(), name='apply-discount'),
    path('remove', RemoveExpiredView.as_view(), name='remove-item'),
]
