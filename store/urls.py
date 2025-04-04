from django.urls import path
from .views import StoreItemListView, DiscountView, RemoveExpiredView, SellStoreItemView, TransferToWarehouseView, ScanBarcodeView

urlpatterns = [
    path('items', StoreItemListView.as_view(), name='store-items'),
    path('discount', DiscountView.as_view(), name='apply-discount'),
    path('remove', RemoveExpiredView.as_view(), name='remove-item'),
    path('transfer-to-warehouse', TransferToWarehouseView.as_view(), name='transfer-to-warehouse'),
    path('sell', SellStoreItemView.as_view(), name='sell-product'),
    path('scan/<str:barcode>', ScanBarcodeView.as_view(), name='scan-barcode'),
]
