from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    RegisterForm, EmailAuthenticationForm, PasswordResetRequestForm,
    PasswordResetConfirmForm, ProfileForm,
)
from .models import CustomUser, PasswordResetOTP


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to Delisushio! Your account was created.')
            return redirect('products:list')
    else:
        form = RegisterForm()
    return render(request, 'authentication/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Logged in successfully.')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('products:list')
    else:
        form = EmailAuthenticationForm(request)
    return render(request, 'authentication/login.html', {'form': form})


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('products:list')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('authentication:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'authentication/profile.html', {'form': form})


def password_reset_request_view(request):
    """Step 1: user submits their email, we generate + email a 6-digit OTP."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                PasswordResetOTP.generate_for_user(user)
                # In production this is sent by email (see signals.py for the
                # DRF-triggered flow); here we handle it directly for the
                # server-rendered form so the OTP is issued immediately.
                otp = user.password_reset_otps.filter(is_used=False).first()
                if otp:
                    print(f"[DEV] Password reset code for {email}: {otp.code}")
            # Always show the same message to avoid leaking which emails exist.
            messages.success(request, 'If that email exists, a reset code has been sent.')
            return redirect('authentication:password_reset_confirm')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'authentication/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request):
    """Step 2: user enters the OTP + new password."""
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            code = form.cleaned_data['code']
            user = CustomUser.objects.filter(email=email).first()
            otp = None
            if user:
                otp = PasswordResetOTP.objects.filter(user=user, code=code, is_used=False).first()

            if not otp or not otp.is_valid:
                if otp:
                    otp.attempts += 1
                    otp.save(update_fields=['attempts'])
                messages.error(request, 'That code is invalid or has expired.')
            else:
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                otp.is_used = True
                otp.save(update_fields=['is_used'])
                messages.success(request, 'Password reset. You can now log in.')
                return redirect('authentication:login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'authentication/password_reset_confirm.html', {'form': form})
