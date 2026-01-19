from django.core.validators import RegexValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

name_validator = RegexValidator(
    regex=r"^[A-Za-z]+(?:[A-Za-z]+)*$",
    message="Only letters are allowed.",
    code="invalid_alphabet",
)

sku_validator = RegexValidator(
    regex=r"^[A-Z0-9_./-]+$",
    message="SKU can contain only uppercase letters, numbers, hyphens (-), and underscores (_).",
    code="invalid_sku",
)


formatted_name_validator= RegexValidator(
    regex=r"^[a-zA-Z' -]+$",
    message="Only letters, spaces, hyphens, and apostrophes are allowed.",
)

image_FileExtensionValidator=FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])

def image_size_validator(image):
    # Limit to 5MB
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Image size must be less than {max_size_mb}MB')