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

handler404 = "core.views.error_pages.custom_404_view"

urlpatterns = [
    # path("default-admin/", admin.site.urls),
    path("", include("core.urls.user_urls")),
    path("", include("catalog.urls.user_urls")),
    path("myprofile/", include("users.user_profile.urls")),
    path("myprofile/", include("users.wallet.urls")),
    path("accounts/", include("allauth.urls")),
    path("adminpanel/accounts/", include("accounts.admin_urls")),
    path("adminpanel/", include("core.urls.admin_urls")),
    path("adminpanel/catalog/", include("catalog.urls.admin_urls")),
    path("", include("users.wishlist.urls")),
    path("", include("users.cart.urls")),
    path("", include("orders.urls.user_urls")),
    path("adminpanel/", include("orders.urls.admin_urls")),
    path("adminpanel/", include("payments.urls")),
    path("adminpanel/", include("offers.urls.admin_urls")),
    path("adminpanel/", include("coupons.urls.admin_urls")),
    path("", include("coupons.urls.user_urls")),
]
