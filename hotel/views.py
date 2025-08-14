from django.contrib import messages
from django.contrib.auth import login
import requests
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404

from users.emails import send_activation_email
from .models import Profile, Room, Reservation, RoomDaySlot
from .forms import UserRegisterForm, ReservationForm, ContactForm
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm, ProfileForm
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from datetime import date, timedelta
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Count



def home(request):
    def cheapest(room_type):
        return (Room.objects
                .filter(room_type=room_type)
                .order_by("price_per_day", "name")
                .first())

    offer = {
        "yard":   cheapest("yard"),
        "indoor": cheapest("indoor"),
        "kennel": cheapest("kennel"),
    }


    weather_data = None
    try:
        resp = requests.get(
            "https://api.weatherapi.com/v1/current.json",
            params={"key": settings.WEATHER_API_KEY, "q": "Warszawa", "lang": "pl"},
            timeout=5
        )
        if resp.status_code == 200:
            weather_data = resp.json()
    except requests.RequestException:
        pass

    return render(request, "home.html", {
        "offer": offer,
        "weather_data": weather_data,
        "current_time": timezone.localtime(),
    })


def about_view(request):
    return render(request, 'hotel/about.html')

def terms_view(request):
    return render(request, 'terms.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.is_active = False
            user.save()

            Profile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                street=form.cleaned_data['street'],
                city=form.cleaned_data['city'],
                zip_code=form.cleaned_data['zip_code']
            )


            send_activation_email(user, request)

            messages.success(
                request,
                "Zarejestrowano! Sprawdź e-mail i kliknij link aktywacyjny, aby zalogować się."
            )
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'auth/register.html', {'form': form})



class CustomLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = self.request.POST.get("remember_me")
        if remember:
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        return super().form_valid(form)


@login_required
def create_reservation(request):
    room_type = request.GET.get("room_type") or None
    room_id = request.GET.get("room") or None

    if request.method == "POST":
        form = ReservationForm(
            request.POST,
            user=request.user,
            preselected_room_type=room_type,
            preselected_room_id=room_id,
        )
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            try:

                reservation.save()
            except ValidationError as e:
                form.add_error(None, e)
            except IntegrityError:
                form.add_error(None, "Nie udało się zapisać rezerwacji. Spróbuj ponownie.")
            else:

                nights = (reservation.end_date - reservation.start_date).days + 1
                total = reservation.room.price_per_day * nights
                if reservation.user.email:
                    subject = f"Potwierdzenie rezerwacji #{reservation.id}"
                    body = (
                        f"Dziękujemy za rezerwację #{reservation.id}.\n\n"
                        f"Pies: {reservation.dog_name}\n"
                        f"Miejsce: {reservation.room.name} ({reservation.room.get_room_type_display()})\n"
                        f"Termin: {reservation.start_date} → {reservation.end_date} ({nights} doby)\n"
                        f"Cena za dobę: {reservation.room.price_per_day} zł\n"
                        f"Razem: {total:.2f} zł\n\n"
                        f"Podsumowanie online: "
                        f"{request.build_absolute_uri(redirect('reservation_confirmation', pk=reservation.pk).url)}\n"
                    )
                    EmailMessage(
                        subject=subject,
                        body=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[reservation.user.email],
                    ).send(fail_silently=True)


                return redirect("reservation_confirmation", pk=reservation.pk)
    else:
        form = ReservationForm(
            user=request.user,
            preselected_room_type=room_type,
            preselected_room_id=room_id,
        )

    return render(request, "hotel/create_reservation.html", {"form": form})


def room_list(request):
    rooms = Room.objects.all().order_by('room_type', 'name')
    grouped={
        'Pokój w domu': rooms.filter(room_type='indoor'),
        'Wspólny wybieg': rooms.filter(room_type='yard'),
        'Pojedynczy kojec': rooms.filter(room_type='kennel'),
    }
    return render(request, 'hotel/room_list.html', {'grouped_rooms': grouped})



def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            body = (
                f"Imię i nazwisko: {data['fullname']}\n"
                f"Email: {data['email']}\n"
                f"Telefon: {data.get('phone','')}\n\n"
                f"Wiadomość:\n{data['message']}"
            )

            msg = EmailMessage(
                subject=f"[Kontakt] {data['subject']}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[getattr(settings, "CONTACT_TO_EMAIL", "kontakt@psihotel.pl")],
                reply_to=[data["email"]],
            )
            msg.send(fail_silently=False)

            messages.success(request, "Dziękujemy! Wiadomość została wysłana.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "hotel/contact.html", {"form": form})


@login_required
def account_overview(request):
    # skrót profilu + 5 ostatnich rezerwacji
    profile = get_object_or_404(Profile, user=request.user)
    last_reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related("room")
        .order_by("-start_date", "-created_at")[:5]
    )
    return render(request, "account/overview.html", {
        "profile": profile,
        "reservations": last_reservations,
    })

@login_required
def account_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("account_overview")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "account/profile_form.html", {"form": form})


@login_required
def account_reservations(request):
    qs = (
        Reservation.objects.filter(user=request.user)
        .select_related("room")
        .order_by("-start_date", "-created_at")
    )
    page = request.GET.get("page")
    paginator = Paginator(qs, 10)
    reservations_page = paginator.get_page(page)

    rows = []
    for r in reservations_page:
        days = (r.end_date - r.start_date).days
        price = (r.room.price_per_day or 0)
        total = days * price if days > 0 else 0
        rows.append({"obj": r, "days": days, "total": total})

    return render(request, "account/reservations.html", {
        "reservations": reservations_page,
        "rows": rows,
    })

@require_GET
def availability_api(request):

    room_id = request.GET.get("room")
    if not room_id:
        return JsonResponse({"error": "Parametr 'room' jest wymagany."}, status=400)

    room = get_object_or_404(Room, pk=room_id)

    def parse_date(s, default):
        if not s:
            return default
        try:
            return date.fromisoformat(s)
        except ValueError:
            raise ValidationError(f"Nieprawidłowy format daty: {s} (oczekiwano YYYY-MM-DD)")

    today = timezone.localdate()
    start = parse_date(request.GET.get("start"), today)
    end = parse_date(request.GET.get("end"), today + timedelta(days=30))

    if end < start:
        return JsonResponse({"error": "Parametr 'end' nie może być wcześniejszy niż 'start'."}, status=400)

    # twarde ograniczenie zakresu
    if (end - start).days > 92:
        return JsonResponse({"error": "Zakres nie może przekraczać 92 dni."}, status=400)

    # policz zajęte sloty per dzień
    taken_per_day = (
        RoomDaySlot.objects
        .filter(room=room, date__gte=start, date__lte=end)
        .values("date")
        .annotate(taken=Count("id"))
    )
    taken_map = {row["date"]: row["taken"] for row in taken_per_day}

    # zbuduj listę dni
    days = []
    d = start
    while d <= end:
        taken = taken_map.get(d, 0)
        free = max(room.capacity - taken, 0)
        days.append({"date": d.isoformat(), "taken": taken, "free": free})
        d += timedelta(days=1)

    return JsonResponse({
        "room": room.id,
        "room_name": room.name,
        "capacity": room.capacity,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days": days,
    })

@login_required
def reservation_confirmation(request, pk):

    reservation = get_object_or_404(
        Reservation.objects.select_related("room"),
        pk=pk,
        user=request.user,
    )
    nights = (reservation.end_date - reservation.start_date).days + 1
    nights = max(nights, 1)
    total = reservation.room.price_per_day * nights

    context = {
        "reservation": reservation,
        "nights": nights,
        "total": total,
    }
    return render(request, "hotel/reservation_confirmation.html", context)


@login_required
def checkout_payment(request, reservation_id):

    reservation = get_object_or_404(
        Reservation.objects.select_related("room"),
        pk=reservation_id,
        user=request.user,
    )
    nights = (reservation.end_date - reservation.start_date).days + 1
    nights = max(nights, 1)
    amount = reservation.room.price_per_day * nights

    return render(request, "hotel/payments/checkout.html", {
        "reservation": reservation,
        "amount": amount,
    })