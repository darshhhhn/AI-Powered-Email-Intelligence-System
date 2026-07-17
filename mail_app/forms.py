from django import forms
from django.contrib.auth import authenticate

from .models import MailConfig


class MailConfigForm(forms.ModelForm):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@gmail.com",
                "autocomplete": "username",
            }
        ),
    )
    app_password = forms.CharField(
        label="Password / App password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Use a Gmail App Password if 2FA is on",
                "autocomplete": "current-password",
            }
        ),
    )

    class Meta:
        model = MailConfig
        fields = ["email", "app_password"]


class UsernameAuthenticationForm(forms.Form):
    """
    Login form for Django auth, matching the existing `mail_app/login.html` template:
    the template expects `form.email` and `form.password` fields.

    We authenticate using Django's username/password under the hood.
    """

    email = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "your username",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your password",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Please enter a correct username and password.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            if not user.is_active:
                raise forms.ValidationError(self.error_messages["inactive"], code="inactive")
            self.user_cache = user
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
