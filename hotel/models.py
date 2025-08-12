from django.conf import settings
from django.db import models, transaction, IntegrityError
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.exceptions import ValidationError



class Profile(models.Model):
    """Represents user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    street = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"




class Room(models.Model):
    """Represents a hotel room where dogs stay."""
    ROOM_TYPE_CHOICES = [
        ('indoor', 'Pokój w domu'),
        ('kennel', 'Pojedynczy kojec'),
        ('yard', 'Wspólny wybieg'),
    ]

    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100, choices=ROOM_TYPE_CHOICES)
    capacity = models.PositiveIntegerField(default=1)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"


class Service(models.Model):
    """Represents an additional service offered during the dog's stay."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.price} zł"





class Reservation(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey("Room", on_delete=models.PROTECT, related_name="reservations")
    dog_name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return f"{self.dog_name} • {self.room} • {self.start_date}–{self.end_date}"


    def clean(self):
        super().clean()
        if self.end_date < self.start_date:
            raise ValidationError("Data zakończenia nie może być wcześniejsza niż data rozpoczęcia.")


        if self.pk:
            orig = Reservation.objects.only("room_id", "start_date", "end_date").get(pk=self.pk)
            if (orig.room_id != self.room_id) or (orig.start_date != self.start_date) or (orig.end_date != self.end_date):
                raise ValidationError("Zmiana pokoju lub zakresu dat nie jest dozwolona – anuluj i utwórz nową rezerwację.")


    def _iter_days(self):
        d = self.start_date
        while d <= self.end_date:
            yield d
            d += timedelta(days=1)

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)


        if is_new:
            try:
                self.allocate_daily_slots()
            except Exception:

                raise

    @transaction.atomic
    def allocate_daily_slots(self):

        for day in self._iter_days():
            allocated = False
            for slot_no in range(1, self.room.capacity + 1):
                try:
                    with transaction.atomic():
                        RoomDaySlot.objects.create(
                            room=self.room,
                            date=day,
                            slot=slot_no,
                            reservation=self,
                        )
                    allocated = True
                    break
                except IntegrityError:

                    continue

            if not allocated:

                RoomDaySlot.objects.filter(reservation=self).delete()
                raise ValidationError(f"Brak wolnych miejsc w {self.room} dnia {day}.")

    @transaction.atomic
    def delete(self, *args, **kwargs):

        RoomDaySlot.objects.filter(reservation=self).delete()
        return super().delete(*args, **kwargs)


class RoomDaySlot(models.Model):

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="day_slots")
    date = models.DateField()
    slot = models.PositiveSmallIntegerField()
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="day_slots"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "date", "slot"], name="unique_room_date_slot"),
        ]
        indexes = [
            models.Index(fields=["room", "date"]),
        ]

    def __str__(self):
        return f"{self.room.name} @ {self.date} [slot {self.slot}] -> {self.reservation_id}"



