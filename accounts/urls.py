from django.urls import path
from .views import RegisterView, VerifyView, LoginView, ResendVerificationView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('verify', VerifyView.as_view(), name='verify'),
    path('login', LoginView.as_view(), name='login'),
    path('resend', ResendVerificationView.as_view(), name='resend-verification'),
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]
