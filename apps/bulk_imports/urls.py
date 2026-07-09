from django.urls import path

from .views import (
    ImportBatchCommitView,
    ImportBatchDetailView,
    ImportBatchListView,
    ImportUploadView,
)


app_name = "bulk_imports"

urlpatterns = [
    path("", ImportBatchListView.as_view(), name="batch_list"),
    path("upload/", ImportUploadView.as_view(), name="upload"),
    path("<int:pk>/", ImportBatchDetailView.as_view(), name="batch_detail"),
    path("<int:pk>/commit/", ImportBatchCommitView.as_view(), name="batch_commit"),
]