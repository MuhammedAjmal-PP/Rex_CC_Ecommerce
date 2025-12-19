from django.urls import path

from pages.views.user_pages import home

urlpatterns = [
    path("", home, name="home"),
]
