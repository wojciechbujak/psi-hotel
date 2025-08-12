from django.contrib import admin
from .models import  Room, Reservation, Service




@admin.register(Room)
class HotelRoomAdmin(admin.ModelAdmin):
    """Admin for HotelRoom model."""
    list_display = ('name', 'room_type', 'capacity')
    list_filter = ('room_type',)
    search_fields = ('name',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin reservation model."""
    list_display = (
        "dog_name",
        "owner_name",
        "owner_email",
        "owner_phone",
        "room",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = ("room__room_type", "room", "start_date", "end_date", "created_at")
    search_fields = ("dog_name", "user__email", "user__username", "user__first_name", "user__last_name", "user__profile__phone_number")
    ordering = ("-start_date", "-created_at")
    date_hierarchy = "start_date"
    list_select_related = ("user", "user__profile", "room")
    readonly_fields = ("user", "created_at")

    fieldsets = (
        ("Właściciel", {"fields": ("user",)}),
        ("Szczegóły pobytu", {"fields": ("dog_name", "room", ("start_date", "end_date"), "notes")}),
        ("Meta", {"fields": ("created_at",)}),
    )

    # ——— kolumny pomocnicze ———
    @admin.display(description="Właściciel")
    def owner_name(self, obj):
        u = obj.user
        full = f"{u.first_name} {u.last_name}".strip()
        return full or u.username

    @admin.display(description="Email")
    def owner_email(self, obj):
        return obj.user.email

    @admin.display(description="Telefon")
    def owner_phone(self, obj):

        return getattr(getattr(obj.user, "profile", None), "phone_number", "")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin for Service model."""
    list_display = ('name', 'price')
    list_filter = ('name',)
