from django.conf import settings
from django.core.validators import MinLengthValidator
from django.forms import ValidationError
from accounts.models import CustomUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from core.validators import min_len_name_validator
from users.user_profile.validators import (
    full_name_validator,
    postal_code_validator,
    address_regex,
    alpha_space_hyphen,
)


class AddressActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Address(models.Model):
    """Users Address for shipping and billing"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    full_name = models.CharField(
        max_length=100, validators=[full_name_validator, min_len_name_validator]
    )
    phone_number = PhoneNumberField()
    address_line_1 = models.CharField(
        max_length=150,
        validators=[
            MinLengthValidator(5, "Address line 1 is too short."),
            address_regex,
        ],
    )
    address_line_2 = models.CharField(
        max_length=150, blank=True, default="", validators=[address_regex]
    )
    city = models.CharField(
        max_length=100, validators=[MinLengthValidator(2), alpha_space_hyphen]
    )
    state = models.CharField(
        max_length=100, validators=[MinLengthValidator(2), alpha_space_hyphen]
    )
    postal_code = models.CharField(
        max_length=6,
        validators=[postal_code_validator],
    )
    country = models.CharField(max_length=5, default="India")

    label = models.CharField(
        max_length=50,
        default="Home",
        blank=True,
        help_text="Address type: Home, Work, or custom label",
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = models.Manager()
    active = AddressActiveManager()

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "Addresses"

    @property
    def snapshot(self):
        """Returns a dict snapshot of the address for order history"""
        return {
            "full_name": self.full_name,
            "phone_number": str(self.phone_number),
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }

    def __str__(self):
        return f"{self.user.email} - {self.full_name} - {self.city}, {self.state}"

    def clean(self):
        super().clean()

        if not self.user_id:
            return
        if self._state.adding:
            active_count = Address.active.filter(user=self.user).count()
            if active_count >= settings.MAX_ADDRESSES_PER_USER:
                raise ValidationError(
                    f"You can only save up to {settings.MAX_ADDRESSES_PER_USER} addresses."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        # 1. Handle Soft Delete (is_active=False)
        if not self.is_active:
            if self.is_default:
                # If we are deleting the default address, promote another one
                other_address = (
                    Address.active.filter(user=self.user)
                    .exclude(pk=self.pk)
                    .order_by("-updated_at")
                    .first()
                )
                if other_address:
                    other_address.is_default = True
                    other_address.save()
                self.is_default = False
        # 2. Handle Active Address Logic
        else:
            has_other_active = (
                Address.active.filter(user=self.user).exclude(pk=self.pk).exists()
            )
            if not has_other_active:
                # If this is the only active address, force it to be default
                self.is_default = True
            elif self.is_default:
                # If this one is set as default, unset others
                Address.active.filter(user=self.user, is_default=True).exclude(
                    pk=self.pk
                ).update(is_default=False)
        super().save(*args, **kwargs)
