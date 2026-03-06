from django.urls import path
from core.views.admin_pages import admin_dashboard, dashboard_chart_data


urlpatterns = [
    path("", admin_dashboard, name="admin_dashboard"),
    path(
        "dashboard/chart-data/",
        dashboard_chart_data,
        name="admin_dashboard_chart_data",
    ),
]
