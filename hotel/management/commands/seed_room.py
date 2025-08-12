from django.core.management.base import BaseCommand
from django.db import transaction
from hotel.models import Room

TARGETS = [
    {"room_type": "indoor", "name": "Pokój", "capacity": 5},
    {"room_type": "kennel", "name": "Kojec", "capacity": 5},
    {"room_type": "yard",   "name": "Wspólny wybieg", "capacity": 10},
]

class Command(BaseCommand):
    help = "Ustala w bazie 3 miejsca: Pokój(5), Kojec(5), Wspólny wybieg(10). Usuwa nadmiarowe wpisy."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0
        deleted = 0

        # 1) Zostaw po 1 rekordzie na typ, resztę usuń (bez slice())
        for rt in ("indoor", "kennel", "yard"):
            qs = Room.objects.filter(room_type=rt).order_by("id")
            if qs.count() > 1:
                keep_id = qs.values_list("id", flat=True).first()
                deleted += Room.objects.filter(room_type=rt).exclude(id=keep_id).delete()[0]

        # 2) Utwórz lub zaktualizuj docelowe rekordy
        for target in TARGETS:
            obj, was_created = Room.objects.get_or_create(
                room_type=target["room_type"],
                defaults={"name": target["name"], "capacity": target["capacity"]},
            )
            if was_created:
                created += 1
            else:
                changes = []
                if obj.name != target["name"]:
                    obj.name = target["name"]; changes.append("name")
                if obj.capacity != target["capacity"]:
                    obj.capacity = target["capacity"]; changes.append("capacity")
                if changes:
                    obj.save(update_fields=changes); updated += 1

        # 3) Usuń cokolwiek o innym room_type (gdyby było)
        valid_types = {t["room_type"] for t in TARGETS}
        extra_qs = Room.objects.exclude(room_type__in=valid_types)
        if extra_qs.exists():
            deleted += extra_qs.delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f"Gotowe. Utworzono: {created}, zaktualizowano: {updated}, usunięto: {deleted}"
        ))
