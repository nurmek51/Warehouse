from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifySerializer, LoginSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from django.core.mail import send_mail
import uuid
import random

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_mail(
                subject='Email Verification',
                message=f'Your verification code: {user.verification_code}',
                from_email='nurmeksdu@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response({"message": "Registration successful, verification email sent"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyView(APIView):
    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            if user.verification_code == serializer.validated_data['verification_code']:
                user.is_verified = True
                user.save()
                return Response({"message": "Email verified"})
            else:
                return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_verified:
                    refresh = RefreshToken.for_user(user)
                    return Response({"token": str(refresh.access_token)})
                else:
                    return Response({"error": "Email not verified"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({"message": "Email already verified"}, status=status.HTTP_400_BAD_REQUEST)
        user.verification_code = str(random.randint(10000, 99999))
        user.save()
        send_mail(
            subject='Resend Email Verification',
            message=f'Your new verification code: {user.verification_code}',
            from_email='nurmeksdu@gmail.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response({"message": "Verification email resent"}, status=status.HTTP_200_OK)