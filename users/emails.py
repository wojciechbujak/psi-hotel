from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import activation_token

def _absolute_url(path: str, request=None) -> str:
    if request is not None:
        return request.build_absolute_uri(path)

    domain = getattr(settings, "SITE_DOMAIN", "psihotel.ovh")
    scheme = "https" if getattr(settings, "USE_HTTPS", True) else "http"
    return f"{scheme}://{domain}{path}"

def send_activation_email(user, request=None) -> bool:
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = activation_token.make_token(user)
    path = reverse("users:activate", kwargs={"uidb64": uidb64, "token": token})
    activate_url = _absolute_url(path, request)

    ctx = {"user": user, "activate_url": activate_url, "site_name": "Psie Hotel"}
    subject = render_to_string("emails/activation_subject.txt", ctx).strip()
    text_body = render_to_string("emails/activation.txt", ctx)
    html_body = render_to_string("emails/activation.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")

    msg.bcc = ["rezerwacje@psihotel.ovh"]
    msg.extra_headers = {"Reply-To": "rezerwacje@psihotel.ovh"}
    return msg.send() == 1
