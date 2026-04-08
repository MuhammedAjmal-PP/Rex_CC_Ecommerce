import re
from django import forms
from reviews.models import Review

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.HiddenInput(),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Sum up your experience...",
                    "maxlength": 120,
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell other collectors about this timepiece...",
                    "rows": 4,
                    "maxlength": 1000,
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError("Please select a rating between 1 and 5.")
        return rating

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("Please provide a review title.")
        if len(title) < 3:
            raise forms.ValidationError(
                "Title is too short (minimum 3 characters)."
            )
        if not re.search(r"[a-zA-Z]", title):
            raise forms.ValidationError("Title must contain at least one letter.")
        return title

    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "").strip()
        if not comment:
            raise forms.ValidationError("Please share your experience.")
        if len(comment) < 10:
            raise forms.ValidationError(
                "Comment is too short (minimum 10 characters)."
            )
        return comment
