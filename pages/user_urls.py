from django.urls import path

from .views.user_pages import home

urlpatterns = [
    path("",home,name="home"),
]