from rest_framework import serializers
from .models import User
import random

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'username')
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False},
        }

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data.get('username', ''),
            is_verified=False
        )
        user.set_password(validated_data['password'])
        user.verification_code = str(random.randint(10000, 99999))
        user.save()
        return user


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
