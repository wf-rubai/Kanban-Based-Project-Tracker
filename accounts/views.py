from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegisterForm, LoginForm, ForgotPasswordForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_manager")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["username"].strip()
        password = form.cleaned_data["password"]
        remember = form.cleaned_data["remember_me"]

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            # allow logging in with email too
            try:
                matched = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=matched.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect("projects:project_manager")
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_manager")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created successfully. Welcome!")
        return redirect("projects:project_manager")

    return render(request, "accounts/register.html", {"form": form})


def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        messages.success(
            request,
            "If an account with that email exists, password reset instructions "
            "have been sent (UI demonstration only).",
        )
        return redirect("accounts:login")
    return render(request, "accounts/forgot_password.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")
