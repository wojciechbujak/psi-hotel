from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .tokens import activation_token

User = get_user_model()

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and activation_token.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
            login(request, user)
            messages.success(request, "Konto zostało aktywowane. Witamy! 🐶")
        else:
            messages.info(request, "To konto jest już aktywne.")
        return redirect("home")
    else:
        return render(request, "users/activation_invalid.html", status=400)
