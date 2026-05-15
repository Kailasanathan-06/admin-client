from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from scanner_api import templates

urlpatterns = [
    path("api/", include("scanner_api.urls")),
    path("login/", templates.login_view, name="login"),
    path("logout/", templates.logout_view, name="logout"),
    path("", templates.dashboard, name="dashboard"),
    path("client/<str:key>/", templates.client_detail, name="client-detail"),
    path("settings/", templates.settings_page, name="settings"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
