from django.core.validators import RegexValidator, MinLengthValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings

name_validator = RegexValidator(
    regex=r"^[A-Za-z]+(?:[A-Za-z]+)*$",
    message="Only letters are allowed.",
    code="invalid_alphabet",
)

full_name_validator = RegexValidator(
    regex=r"^[A-Za-zÀ-ÿ]+([-'\s][A-Za-zÀ-ÿ]+)*$",
    message="Name must start with a letter and can only contain letters, hyphens, apostrophes, and spaces.",
    code="invalid_full_name",
)

min_len_name_validator = MinLengthValidator(
    3, message="Name must contain at least 3 letters"
)

postal_code_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="Postal code must be exactly 6 digits",
    code="Invalid_code",
)

sku_validator = RegexValidator(
    regex=r"^[A-Z0-9_./-]+$",
    message="SKU can contain only uppercase letters, numbers, hyphens (-), and underscores (_).",
    code="invalid_sku",
)


formatted_name_validator = RegexValidator(
    regex=r"^[a-zA-Z' -]+$",
    message="Only letters, spaces, hyphens, and apostrophes are allowed.",
)

# ========= Image Validator ========#

image_file_extension_validator = FileExtensionValidator(
    allowed_extensions=[ext.lower() for ext in settings.ALLOWED_IMAGE_EXTENSIONS]
)


def image_size_validator(image):
    max_size_mb = getattr(settings, "IMAGE_MAX_SIZE_MB", 3)
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size must be less than {max_size_mb}MB")
