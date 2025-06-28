from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'placeholder': ' ',
            'class': 'form-control input-with-icon',
            'autocomplete': 'email'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company', 'position', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле username из формы
        #del self.fields['username']


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'placeholder': ' ',
            'class': 'form-control input-with-icon',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': ' ',
            'class': 'form-control input-with-icon',
            'autocomplete': 'current-password'
        }),
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }