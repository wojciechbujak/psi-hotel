from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_booking_confirmation(booking):

    ctx = {
        "client_name": getattr(booking, "customer_name", ""),
        "dog_name": getattr(booking, "dog_name", ""),
        "check_in": getattr(booking, "check_in", None),
        "check_out": getattr(booking, "check_out", None),
        "booking_id": getattr(booking, "id", None),
        "site_name": "Psie Hotel",
    }

    subject = f"Potwierdzenie rezerwacji #{ctx['booking_id']} – {ctx['site_name']}"
    text_body = render_to_string("emails/booking_confirmation.txt", ctx)
    html_body = render_to_string("emails/booking_confirmation.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[getattr(booking, "customer_email", "")],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
