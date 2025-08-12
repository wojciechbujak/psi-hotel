from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .forms import PasswordResetForm
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),

    path('reservations/new/', views.create_reservation, name='create_reservation'),
    path('rooms/', views.room_list, name='room_list'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("account/", views.account_overview, name="account_overview"),
    path("account/profile/", views.account_profile, name="account_profile"),
    path("account/reservations/", views.account_reservations, name="account_reservations"),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=PasswordResetForm,  # <— ważne
            template_name="auth/password_reset_form.html",
            email_template_name="auth/password_reset_email.html",
            subject_template_name="auth/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),

    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="auth/password_reset_done.html",
         ),
         name="password_reset_done"),

    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="auth/password_reset_confirm.html",
             success_url="/reset/done/",
         ),
         name="password_reset_confirm"),

    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="auth/password_reset_complete.html",
         ),
         name="password_reset_complete"),
    path("api/availability/", views.availability_api, name="availability_api"),

    path("reservations/<int:pk>/confirmation/", views.reservation_confirmation, name="reservation_confirmation"),
    path("payments/checkout/<int:reservation_id>/", views.checkout_payment, name="checkout_payment"),


]