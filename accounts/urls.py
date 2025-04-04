from .views import RegisterView, VerifyView, LoginView, ResendVerificationView
from django.urls import path

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('verify', VerifyView.as_view(), name='verify'),
    path('login', LoginView.as_view(), name='login'),
    path('resend', ResendVerificationView.as_view(), name='resend-verification'),
]
