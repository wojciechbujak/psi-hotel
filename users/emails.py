# users/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

from .tokens import account_activation_token

def send_activation_email(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
    activate_url = request.build_absolute_uri(path)

    ctx = {"user": user, "activate_url": activate_url, "site_name": "Psie Hotel"}
    subject = f"Potwierdź rejestrację – {ctx['site_name']}"
    text_body = render_to_string("emails/activate.txt", ctx)
    html_body = render_to_string("emails/activate.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
