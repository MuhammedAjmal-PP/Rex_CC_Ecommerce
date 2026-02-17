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
        "transactions/<uuid:txn_id>/",
        transaction_detail,
        name="admin_transaction_detail",
    ),
    path("refunds/", refund_list, name="admin_refund_list"),
    path("refunds/<uuid:txn_id>/", refund_detail, name="admin_refund_detail"),
    path(
        "refunds/<uuid:txn_id>/action/",
        refund_action,
        name="admin_refund_action",
    ),
]
