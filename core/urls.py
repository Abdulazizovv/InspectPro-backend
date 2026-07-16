from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.botapp.views import health_check, bot_status, telegram_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health
    path("health/", health_check, name="health_check"),
    path("bot-status/", bot_status, name="bot_status"),
    # Telegram Webhook
    path("api/telegram/webhook/<str:token>", telegram_webhook, name="telegram_webhook_no_slash"),
    path("api/telegram/webhook/<str:token>/", telegram_webhook, name="telegram_webhook"),
    # API v1
    path("api/v1/", include("apps.branches.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/clients/", include("apps.clients.urls")),
    path("api/v1/vehicles/", include("apps.vehicles.urls")),
    path("api/v1/inspections/", include("apps.inspections.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/reminders/", include("apps.reminders.urls")),
    # API Schema & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
