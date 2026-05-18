from django.urls import path
from . import views

urlpatterns = [
    path("register", views.RegisterClientView.as_view(), name="api-register"),
    path("approve", views.ApproveClientView.as_view(), name="api-approve"),
    path("approve-multiple", views.ApproveMultipleView.as_view(), name="api-approve-multiple"),
    path("ping", views.PingClientView.as_view(), name="api-ping"),
    path("scan", views.SubmitScanView.as_view(), name="api-scan"),
    path("clients", views.ClientListView.as_view(), name="api-clients"),
    path("clients/<str:key>/status", views.ClientStatusView.as_view(), name="api-client-status"),
    path("clients/<str:key>", views.ClientDetailView.as_view(), name="api-client-detail"),
    path("clients/<str:key>/manual", views.ManualUpdateView.as_view(), name="api-manual"),
    path("clients/<str:key>/addons", views.AddonListView.as_view(), name="api-addons"),
    path("clients/<str:key>/addons/<int:addon_id>", views.AddonDeleteView.as_view(), name="api-addon-delete"),
    path("clients/<str:key>/scan-config", views.ScanConfigView.as_view(), name="api-scan-config"),
    path("clients/<str:key>/scan-now", views.TriggerScanView.as_view(), name="api-trigger-scan"),
    path("clients/<str:key>/scan-results", views.ClientScanResultsView.as_view(), name="api-client-scan-results"),
    path("clients/delete-multiple", views.DeleteMultipleView.as_view(), name="api-delete-multiple"),
    path("scan/local", views.LocalScanView.as_view(), name="api-scan-local"),
    path("scan/all", views.ScanAllView.as_view(), name="api-scan-all"),
    path("admin-client", views.AdminClientInfoView.as_view(), name="api-admin-client"),
    path("activity-log", views.ActivityLogView.as_view(), name="api-activity-log"),
    path("groups", views.GroupListView.as_view(), name="api-groups"),
    path("groups/<int:group_id>", views.GroupDeleteView.as_view(), name="api-group-delete"),
    path("settings", views.SettingsView.as_view(), name="api-settings"),
]
