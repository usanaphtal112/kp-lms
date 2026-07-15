from django.urls import path

from .views import (
    ClinicalReportAttachmentDownloadView,
    ClinicalReportCreateView,
    ClinicalReportDetailView,
    ClinicalReportExportView,
    ClinicalReportListView,
    ClinicalReportReviewView,
    ClinicalReportSubmitView,
    ClinicalReportUpdateView,
    ClinicalTeachingReportCreateView,
    ClinicalTeachingReportDetailView,
    ClinicalTeachingReportExportView,
    ClinicalTeachingReportListView,
    ClinicalTeachingReportReviewView,
    ClinicalTeachingReportSubmitView,
    ClinicalTeachingReportUpdateView,
    MyPortfolioView,
    PortfolioExportView,
    PortfolioItemCreateView,
    ReportsDashboardView,
    StudentPortfolioView,
    TeachingReportAttachmentDownloadView,
)


app_name = "reports"

urlpatterns = [
    path("", ReportsDashboardView.as_view(), name="dashboard"),

    path("clinical/", ClinicalReportListView.as_view(), name="clinical_report_list"),
    path("clinical/create/", ClinicalReportCreateView.as_view(), name="clinical_report_create"),
    path("clinical/<int:pk>/", ClinicalReportDetailView.as_view(), name="clinical_report_detail"),
    path("clinical/<int:pk>/update/", ClinicalReportUpdateView.as_view(), name="clinical_report_update"),
    path("clinical/<int:pk>/submit/", ClinicalReportSubmitView.as_view(), name="clinical_report_submit"),
    path("clinical/<int:pk>/review/", ClinicalReportReviewView.as_view(), name="clinical_report_review"),
    path("clinical/<int:pk>/download/", ClinicalReportAttachmentDownloadView.as_view(), name="clinical_report_download"),
    path("clinical/export/", ClinicalReportExportView.as_view(), name="clinical_report_export"),

    path("teaching/", ClinicalTeachingReportListView.as_view(), name="teaching_report_list"),
    path("teaching/create/", ClinicalTeachingReportCreateView.as_view(), name="teaching_report_create"),
    path("teaching/<int:pk>/", ClinicalTeachingReportDetailView.as_view(), name="teaching_report_detail"),
    path("teaching/<int:pk>/update/", ClinicalTeachingReportUpdateView.as_view(), name="teaching_report_update"),
    path("teaching/<int:pk>/submit/", ClinicalTeachingReportSubmitView.as_view(), name="teaching_report_submit"),
    path("teaching/<int:pk>/review/", ClinicalTeachingReportReviewView.as_view(), name="teaching_report_review"),
    path("teaching/<int:pk>/download/", TeachingReportAttachmentDownloadView.as_view(), name="teaching_report_download"),
    path("teaching/export/", ClinicalTeachingReportExportView.as_view(), name="teaching_report_export"),

    path("portfolio/", MyPortfolioView.as_view(), name="my_portfolio"),
    path("portfolio/export/", PortfolioExportView.as_view(), name="my_portfolio_export"),
    path("portfolio/items/create/", PortfolioItemCreateView.as_view(), name="my_portfolio_item_create"),

    path("portfolio/students/<int:student_pk>/", StudentPortfolioView.as_view(), name="student_portfolio"),
    path("portfolio/students/<int:student_pk>/export/", PortfolioExportView.as_view(), name="student_portfolio_export"),
    path("portfolio/students/<int:student_pk>/items/create/", PortfolioItemCreateView.as_view(), name="student_portfolio_item_create"),
]