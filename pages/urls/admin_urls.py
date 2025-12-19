from django.urls import path
from pages.views.admin_pages import admin_dashboard


urlpatterns = [
    path("",admin_dashboard,name="admin_dashboard")
]
