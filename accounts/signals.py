"""
Allauth signal handlers for the accounts app.

1. Email change flow: swap primary, blacklist old email.
2. Referral reward: credit both referrer and referee wallets.
"""

from decimal import Decimal
from allauth.account.models import EmailAddress as AllauthEmailAddress
from allauth.account.signals import email_confirmed
from django.conf import settings
from django.db import transaction as db_transaction
from django.dispatch import receiver
from accounts.models import BlacklistedEmail
from payments.service import create_transaction
from users.wallet.service import credit_wallet


@receiver(email_confirmed)
def handle_email_confirmed(sender, request, email_address, **kwargs):
    """
    Fired every time an EmailAddress is confirmed.

    1. Email-change flow: if confirmed email ≠ current email → swap + blacklist + remove old.
    2. Referral reward: if user has referred_by and hasn't been rewarded yet.
    """
    user = email_address.user

    # ── 1. Email-change confirmation ──
    if email_address.email != user.email:
        old_email = user.email

        email_address.set_as_primary()
        user.email = email_address.email
        user.save(update_fields=["email"])

        BlacklistedEmail.objects.get_or_create(
            email=old_email,
            defaults={"original_user": user, "reason": "EMAIL_CHANGED"},
        )

        # Remove the old email from allauth's EmailAddress table
        AllauthEmailAddress.objects.filter(user=user, email=old_email).delete()

        return  # done — don't process referral on email change

    # ── 2. Referral reward (first-time email verification only) ──
    if not user.referred_by:
        return

    # Guard: only reward once — check if a REFERRAL_REWARD txn already exists
    from payments.models import Transaction

    already_rewarded = Transaction.objects.filter(
        user=user, transaction_type="REFERRAL_REWARD"
    ).exists()

    if already_rewarded:
        return

    referrer = user.referred_by

    # Fix #16: wrap both credits in a single atomic block
    with db_transaction.atomic():
        reward = Decimal(settings.REFERRAL_REWARD_AMOUNT)

        # Credit referee (new user)
        referee_txn = create_transaction(
            user=user,
            txn_type="REFERRAL_REWARD",
            method="WALLET",
            amount=reward,
            status="COMPLETED",
            content_object=user,
            note=f"Referral reward — referred by {referrer.email}",
        )
        credit_wallet(
            user=user, amount=reward, transaction_obj=referee_txn
        )

        # Credit referrer (existing user)
        referrer_txn = create_transaction(
            user=referrer,
            txn_type="REFERRAL_REWARD",
            method="WALLET",
            amount=reward,
            status="COMPLETED",
            content_object=referrer,
            note=f"Referral reward — {user.email} joined using your code",
        )
        credit_wallet(
            user=referrer, amount=reward, transaction_obj=referrer_txn
        )
