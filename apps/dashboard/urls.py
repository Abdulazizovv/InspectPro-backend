from django.urls import path
from .views import DashboardStatsView, ReportsView, SiteSettingsView

urlpatterns = [
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("reports/", ReportsView.as_view(), name="dashboard-reports"),
    path("settings/", SiteSettingsView.as_view(), name="site-settings"),
]
