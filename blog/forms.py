from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .access import is_blog_owner
from .models import post


class OwnerAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-input", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-input", "autocomplete": "current-password"}
        )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not is_blog_owner(user):
            raise forms.ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


class ArticleForm(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "id": "id_title",
                "class": "editor-title-input",
                "placeholder": "Give your article a title...",
                "autocomplete": "off",
            }
        ),
    )
    body = forms.CharField(
        strip=False,
        widget=forms.Textarea(
            attrs={
                "id": "id_body",
                "class": "editor-body-input",
                "rows": 22,
                "placeholder": "Write your article here...",
                "spellcheck": "true",
            }
        ),
    )

    class Meta:
        model = post
        fields = ("title", "body")

    def clean_body(self):
        body = self.cleaned_data["body"]
        if not body.strip():
            raise forms.ValidationError("Write some content before saving.")
        return body
