from django.urls import path
from . import views

app_name = "users"
urlpatterns = [
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
]
