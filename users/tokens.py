from django.contrib.auth.tokens import PasswordResetTokenGenerator

class ActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        email = getattr(user, "email", "") or ""
        return f"{user.pk}{timestamp}{user.is_active}{email}"

activation_token = ActivationTokenGenerator()
