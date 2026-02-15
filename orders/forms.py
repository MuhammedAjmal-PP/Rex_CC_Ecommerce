from django import forms
from orders.models import Return

MAX_RETURN_IMAGES = 3


class ReturnForm(forms.ModelForm):
    """
    Form for submitting a return request.
    Photos are handled separately via raw HTML input + view-level validation.
    """

    class Meta:
        model = Return
        fields = ["reason_code", "comment"]
        widgets = {
            "reason_code": forms.Select(
                attrs={
                    "class": "form-control",
                },
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "maxlength": 1000,
                    "placeholder": "Tell us more about the issue",
                },
            ),
        }
        labels = {
            "reason_code": "Reason for return",
            "comment": "Additional details",
        }

    def clean_reason_code(self):
        reason_code = self.cleaned_data.get("reason_code")
        if not reason_code:
            raise forms.ValidationError("Please select a reason for the return.")
        return reason_code

    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "").strip()
        reason_code = self.data.get("reason_code", "")
        if reason_code == "OTHER" and not comment:
            raise forms.ValidationError(
                "Please provide details when selecting 'Other' as a reason."
            )
        return comment or None
