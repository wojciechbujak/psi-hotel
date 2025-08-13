
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .tokens import account_activation_token

User = get_user_model()

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return HttpResponseRedirect(reverse("dashboard"))  # podmień na swój URL
    return HttpResponse("Link nieprawidłowy lub wygasł.", status=400)
