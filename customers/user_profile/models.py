from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Address(models.Model):
    """User shipping/billing addresses"""
    
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, validators=[MinLengthValidator(3)])
    country = models.CharField(max_length=100, default='India')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home')
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = 'Addresses'
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        # If this is the first address, make it default
        elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            self.is_default = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"


class BlockedEmail(models.Model):
    """Track old emails that have been changed to prevent reuse"""
    
    email = models.EmailField(unique=True)
    original_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blocked_emails'
    )
    blocked_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, default='Email changed by user')
    
    class Meta:
        ordering = ['-blocked_at']
    
    def __str__(self):
        return f"Blocked: {self.email}"
