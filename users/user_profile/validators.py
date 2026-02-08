from django.core.validators import RegexValidator


full_name_validator = RegexValidator(
    regex=r"^[A-Za-zÀ-ÿ]+([-'\s][A-Za-zÀ-ÿ]+)*$",
    message="Name must start with a letter and can only contain letters, hyphens, apostrophes, and spaces.",
    code="invalid_full_name",
)

postal_code_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="Postal code must be exactly 6 digits",
    code="Invalid_code",
)

# Common regex for city and state names
alpha_space_hyphen = RegexValidator(
    regex=r"^[a-zA-Z\s\-]+$",
    message="This field should only contain letters, spaces, and hyphens.",
)

# Regex for address line 1 (allows letters, numbers, spaces, and common symbols like # , -)
address_regex = RegexValidator(
    regex=r"^[a-zA-Z0-9\s\.,#\-]+$", message="Address contains unsupported characters."
)
