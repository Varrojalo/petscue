from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm


class EmailAdminAuthenticationForm(AdminAuthenticationForm):
    """Accounts sign in with their person's email, so the login form asks for an email."""

    username = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))
