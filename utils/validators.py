from django.core.validators import RegexValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings

name_validator = RegexValidator(
    regex=r"^[A-Za-z]+(?:[A-Za-z]+)*$",
    message="Only letters are allowed.",
    code="invalid_alphabet",
)


def name_size_validator(name):
    if len(name) < 3:
        raise ValidationError("Name must contain at least 3 letters", code="min_length")


sku_validator = RegexValidator(
    regex=r"^[A-Z0-9_./-]+$",
    message="SKU can contain only uppercase letters, numbers, hyphens (-), and underscores (_).",
    code="invalid_sku",
)


formatted_name_validator = RegexValidator(
    regex=r"^[a-zA-Z' -]+$",
    message="Only letters, spaces, hyphens, and apostrophes are allowed.",
)

#========= Image Validator ========#

image_file_extension_validator = FileExtensionValidator(
    allowed_extensions=[ ext.lower() for ext in settings.ALLOWED_IMAGE_EXTENSIONS]
)


def image_size_validator(image):
    max_size_mb = getattr(settings, "IMAGE_MAX_SIZE_MB", 3)
    if image.size >  max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size must be less than {max_size_mb}MB")
