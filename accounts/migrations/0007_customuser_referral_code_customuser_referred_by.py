"""
Add referral_code and referred_by to CustomUser.

Three-step migration:
1. Add referral_code as non-unique + referred_by FK
2. Populate referral_code for existing users
3. Add unique constraint on referral_code
"""

import string

from django.db import migrations, models
import django.db.models.deletion
from django.utils.crypto import get_random_string


def populate_referral_codes(apps, schema_editor):
    """Generate unique referral codes for all existing users."""
    CustomUser = apps.get_model("accounts", "CustomUser")
    chars = string.ascii_uppercase + string.digits
    existing_codes = set()

    for user in CustomUser.objects.all():
        if user.referral_code:
            existing_codes.add(user.referral_code)
            continue

        # Generate unique code
        for _ in range(20):
            code = "REX-" + get_random_string(6, chars)
            if code not in existing_codes:
                break
        existing_codes.add(code)
        user.referral_code = code
        user.save(update_fields=["referral_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_blacklistedemail"),
    ]

    operations = [
        # Step 1: Add fields WITHOUT unique constraint
        migrations.AddField(
            model_name="customuser",
            name="referral_code",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                help_text="Auto-generated unique referral code",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="referred_by",
            field=models.ForeignKey(
                blank=True,
                help_text="User who referred this account",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referrals",
                to="accounts.customuser",
            ),
        ),
        # Step 2: Populate existing users
        migrations.RunPython(
            populate_referral_codes,
            migrations.RunPython.noop,
        ),
        # Step 3: Add unique constraint
        migrations.AlterField(
            model_name="customuser",
            name="referral_code",
            field=models.CharField(
                blank=True,
                editable=False,
                help_text="Auto-generated unique referral code",
                max_length=10,
                unique=True,
            ),
        ),
    ]
