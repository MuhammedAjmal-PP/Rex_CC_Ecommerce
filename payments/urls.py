from django.urls import path
from payments.views import (
    transaction_list,
    transaction_detail,
    refund_list,
    refund_detail,
    refund_action,
)

urlpatterns = [
    path("transactions/", transaction_list, name="admin_transaction_list"),
    path(
        "transactions/<str:txn_id>/",
        transaction_detail,
        name="admin_transaction_detail",
    ),
    path("refunds/", refund_list, name="admin_refund_list"),
    path("refunds/<str:txn_id>/", refund_detail, name="admin_refund_detail"),
    path(
        "refunds/<str:txn_id>/action/",
        refund_action,
        name="admin_refund_action",
    ),
]
