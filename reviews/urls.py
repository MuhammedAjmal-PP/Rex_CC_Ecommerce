from django.urls import path

from reviews import views

app_name = "reviews"

urlpatterns = [
    path(
        "review/<int:product_id>/submit/",
        views.submit_review,
        name="submit_review",
    ),
]
