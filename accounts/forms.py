import random

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

AVATAR_COLORS = ["#2F81F7", "#3FB950", "#D29922", "#F85149", "#A371F7", "#DB61A2"]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Full name")

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.avatar_color = random.choice(AVATAR_COLORS)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False, initial=True)


class ForgotPasswordForm(forms.Form):
    """UI-only form as specified — no email is actually sent."""
    email = forms.EmailField(label="Account email")
