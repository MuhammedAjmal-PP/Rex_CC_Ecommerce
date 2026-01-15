"""
URL configuration for rexcc_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("default-admin/", admin.site.urls),
    path("", include("pages.urls.user_urls")),
    path("", include("catalog.urls.user_urls")),
    path("accounts/", include("customers.user_profile.urls")),
    path("accounts/", include("allauth.urls")),
    path("adminpanel/accounts/", include("accounts.admin_urls")),
    path("adminpanel/", include("pages.urls.admin_urls")),
    path("adminpanel/catalog/", include("catalog.urls.admin_urls")),
]
