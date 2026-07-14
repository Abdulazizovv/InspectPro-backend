from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SmsReminderViewSet, SmsTemplateViewSet

router = DefaultRouter()
router.register("templates", SmsTemplateViewSet, basename="sms-template")
router.register("", SmsReminderViewSet, basename="reminder")

urlpatterns = [
    path("", include(router.urls)),
]
