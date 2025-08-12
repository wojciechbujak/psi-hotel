
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import Profile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Imię')
    last_name  = forms.CharField(label='Nazwisko')
    email      = forms.EmailField(required=True, label='Adres e-mail')

    phone_number = forms.CharField(label='Numer telefonu', required=False)
    street       = forms.CharField(label='Ulica', required=False)
    city         = forms.CharField(label='Miasto', required=False)
    zip_code     = forms.CharField(label='Kod pocztowy', required=False)

    password1 = forms.CharField(
        label='Hasło',
        widget=forms.PasswordInput,
        help_text=''
    )
    password2 = forms.CharField(
        label='Potwierdź hasło',
        widget=forms.PasswordInput,
        help_text='Wpisz ponownie to samo hasło'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Konto z tym adresem e-mail już istnieje.')
        return email

    def clean_password2(self):
        pwd1 = self.cleaned_data.get('password1')
        pwd2 = self.cleaned_data.get('password2')

        if pwd1 and pwd2 and pwd1 != pwd2:
            raise forms.ValidationError('Hasła nie są identyczne.')


        validate_password(pwd1, user=None)
        return pwd2

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        email = (self.cleaned_data.get('email') or '').lower().strip()
        user.username  = email
        user.email     = email
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')

        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': self.cleaned_data.get('phone_number', ''),
                    'street':       self.cleaned_data.get('street', ''),
                    'city':         self.cleaned_data.get('city', ''),
                    'zip_code':     self.cleaned_data.get('zip_code', ''),
                }
            )
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = """
        Hasło musi:
        <ul>
            <li>zawierać co najmniej 10 znaków,</li>
            <li>nie składać się wyłącznie z cyfr.</li>
        </ul>
        """

        for name, field in self.fields.items():
            base = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (base + ' form-control border-0 border-bottom rounded-0').strip()
            field.widget.attrs.setdefault('placeholder', field.label)




from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Reservation, Room


class ReservationForm(forms.ModelForm):
    dog_name = forms.CharField(
        label="Imię psa",
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Np. Burek"
        })
    )

    class Meta:
        model = Reservation
        fields = ["dog_name", "room", "start_date", "end_date", "notes"]
        labels = {
            "room": "Miejsce",
            "start_date": "Od",
            "end_date": "Do",
            "notes": "Uwagi",
        }
        widgets = {
            "room": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Uwagi (opcjonalnie)"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        preselected_room_type = kwargs.pop("preselected_room_type", None)
        preselected_room_id = kwargs.pop("preselected_room_id", None)
        super().__init__(*args, **kwargs)


        qs = Room.objects.all().order_by("room_type", "name")

        if preselected_room_type:
            qs = qs.filter(room_type=preselected_room_type)
            if qs.exists():
                self.fields["room"].initial = qs.first().pk

        # Jeśli podano konkretne ID pokoju
        if preselected_room_id:
            qs = Room.objects.filter(pk=preselected_room_id)
            if qs.exists():
                self.fields["room"].initial = preselected_room_id

        self.fields["room"].queryset = qs


        def label_from_instance(obj: Room):
            return f"{obj.get_room_type_display()} – {obj.price_per_day} zł/doba"
        self.fields["room"].label_from_instance = label_from_instance

        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        self.fields["start_date"].widget.attrs["min"] = today.isoformat()
        self.fields["end_date"].widget.attrs["min"] = tomorrow.isoformat()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        if start and start < today:
            self.add_error("start_date", "Data początkowa nie może być wcześniejsza niż dzisiaj.")

        if end and end < tomorrow:
            self.add_error("end_date", "Data zakończenia musi być co najmniej jutro.")

        if start and end and end <= start:
            self.add_error("end_date", "Data zakończenia musi być po dacie początkowej.")

        return cleaned





class ContactForm(forms.Form):
    fullname = forms.CharField(label="Imię i nazwisko")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Numer telefonu", required=False)
    subject = forms.CharField(label="Temat")
    message = forms.CharField(label="Wiadomość", widget=forms.Textarea)

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adres e-mail",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "autocomplete": "email",
        })
    )
    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "autocomplete": "current-password",
        })
    )

class PasswordResetForm(DjangoPasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Adres e-mail'
        })



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone_number", "street", "city", "zip_code"]
        labels = {
            "phone_number": "Telefon",
            "street": "Ulica",
            "city": "Miasto",
            "zip_code": "Kod pocztowy",
        }
        widgets = {
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "123-456-789"}),
            "street": forms.TextInput(attrs={"class": "form-control", "placeholder": "ul. Przykładowa 1"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Warszawa"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "00-000"}),
        }
