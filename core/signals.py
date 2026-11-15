from threading import Thread

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@receiver(post_save, sender=get_user_model())
def send_welcome_email(sender, instance, created, **kwargs):
    if not created or instance.is_superuser or not instance.email:
        return

    uid = urlsafe_base64_encode(force_bytes(instance.pk))
    token = default_token_generator.make_token(instance)
    reset_path = reverse(
        'password_reset_confirm',
        kwargs={'uidb64': uid, 'token': token},
    )
    reset_url = f"https://{settings.SITE_DOMAIN}{reset_path}"
    portal_url = f"https://{settings.SITE_DOMAIN}"
    message = (
        f"Hello {instance.username},\n\n"
        "Welcome to the Student Performance Management System. "
        f"Set your password using this secure link:\n{reset_url}\n\n"
        f"Visit the portal at {portal_url}."
    )

    Thread(
        target=send_mail,
        kwargs={
            'subject': 'Welcome to the SPMS Portal',
            'message': message,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'recipient_list': [instance.email],
        },
        daemon=True,
    ).start()
