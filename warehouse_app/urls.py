from django.urls import path
from .views import (
    FileUploadView,
    UploadListView,
    WarehouseItemsView,
    TransferToStoreView,
    ExpiringItemsView
)

urlpatterns = [
    path('upload', FileUploadView.as_view(), name='file-upload'),
    path('files', UploadListView.as_view(), name='upload-list'),
    path('items/<int:file_id>', WarehouseItemsView.as_view(), name='warehouse-items'),
    path('to-store', TransferToStoreView.as_view(), name='transfer-to-store'),
    path('notifications', ExpiringItemsView.as_view(), name='expiring-items'),
]
