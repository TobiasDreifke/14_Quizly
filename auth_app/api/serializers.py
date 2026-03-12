from rest_framework import serializers
from django.contrib.auth.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration.

    Validates that passwords match and that the email address is not already
    in use. The password and confirmed_password fields are write-only and never
    returned in any response.

    Fields:
        username          – Unique username (validated by Django's User model).
        email             – Required, must be unique across all users.
        password          – Write-only. Stored as a hashed value via set_password().
        confirmed_password – Write-only. Must match password. Not saved to the database.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_confirmed_password(self, value):
        """
        Checks that confirmed_password matches the provided password.
        Raises a ValidationError if they differ.
        """
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """
        Checks that the email address is not already registered.
        Raises a ValidationError if a user with this email already exists.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """
        Creates and saves a new User instance.
        Uses set_password() to ensure the password is properly hashed before saving.
        The confirmed_password field is intentionally excluded from the saved data.
        """
        account = User(
            email=self.validated_data['email'],
            username=self.validated_data['username'],
        )
        account.set_password(self.validated_data['password'])
        account.save()
        return account
