
import datetime as dt
import pytest
from django.contrib.auth import get_user_model
from django.db import transaction
from hotel.models import Room, Reservation  # dostosuj import

User = get_user_model()

@pytest.mark.django_db
def test_cannot_overbook_room_by_slots():
    u = User.objects.create(username="u1")
    room = Room.objects.create(name="Pokój 1", room_type="indoor", capacity=1, price_per_day=100)

    a = Reservation.objects.create(
        user=u, room=room, dog_name="Reksio",
        start_date=dt.date(2025, 8, 10),
        end_date=dt.date(2025, 8, 12),
    )

    with pytest.raises(Exception):
        Reservation.objects.create(
            user=u, room=room, dog_name="Azor",
            start_date=dt.date(2025, 8, 11),
            end_date=dt.date(2025, 8, 13),
        )
