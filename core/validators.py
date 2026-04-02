from django.core.validators import RegexValidator, MinLengthValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

# ========= name Validator ========#

name_validator = RegexValidator(
    regex=r"^[A-Za-z]+(?:[A-Za-z]+)*$",
    message="Only letters are allowed.",
    code="invalid_alphabet",
)

min_len_name_validator = MinLengthValidator(
    3, message="Name must contain at least 3 letters"
)

# ========= Image Validator ========#


def image_file_extension_validator(value):
    allowed_extensions = [ext.lower() for ext in settings.ALLOWED_IMAGE_EXTENSIONS]
    if isinstance(value, UploadedFile):
        FileExtensionValidator(allowed_extensions=allowed_extensions)(value)


def image_size_validator(image):
    max_size_mb = getattr(settings, "IMAGE_MAX_SIZE_MB", 3)
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size must be less than {max_size_mb}MB")
