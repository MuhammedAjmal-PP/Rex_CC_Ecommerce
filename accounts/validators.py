import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class NoWhitespacePasswordValidator:

    def validate(self, password, user=None):
        if password is None:
            return

        trimmed = password.strip()

        if trimmed == "":
            raise ValidationError(
                _("Password is required."),
                code="password_required",
            )

        # Reject whitespace in the middle
        if re.search(r"\s", trimmed):
            raise ValidationError(
                _("Password must not contain spaces."),
                code="password_middle_spaces",
            )

    def get_help_text(self):
        return _("Please remove spaces from your password.")
