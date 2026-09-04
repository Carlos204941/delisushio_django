import logging
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django_rest_passwordreset.signals import reset_password_token_created
from .models import PasswordResetOTP

logger = logging.getLogger(__name__)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Intercepts the default token creation and generates a 6-digit OTP instead.
    """
    user = reset_password_token.user
    otp = PasswordResetOTP.generate_for_user(user)

    context = {
        'user': user,
        'reset_code': otp.code,
        'expiry_minutes': 10,
        'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
    }

    html_message = render_to_string('authentication/password_reset_email.html', context)
    plain_message = render_to_string('authentication/password_reset_email.txt', context)

    try:
        send_mail(
            subject='Your Password Reset Code',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send reset email to {user.email}: {e}")
