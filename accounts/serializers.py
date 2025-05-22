from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from djoser.serializers import UserSerializer

from accounts.models import User


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["is_manager"] = user.is_manager()
        token["is_employee"] = user.is_employee()
        token["is_superuser"] = user.is_superuser
        token["role"] = user.role  # Include the role directly
        token["user_id"] = str(user.id)

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        if not user.is_active:
            raise ValidationError(
                {"message": "This account is inactive. Please contact support."}
            )

        return data


class UserDataSerializer(UserSerializer):
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    is_active = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    employee_id = serializers.UUIDField(read_only=True)
    warehouse_id = serializers.UUIDField(read_only=True)
    is_manager = serializers.SerializerMethodField()
    is_employee = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_superuser",
            "is_manager",
            "is_employee",
            "employee_id",
            "warehouse_id",
        ]

    def get_is_manager(self, user):
        if user.role == User.ROLES.EMPLOYEE_MANAGER:
            return True
        return False

    def get_is_employee(self, user):
        if user.role == User.ROLES.EMPLOYEE:
            return True
        return False


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        style={"input_type": "password"}, required=True
    )
    new_password = serializers.CharField(
        style={"input_type": "password"}, required=True
    )

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise ValidationError({"current_password": "Does not match"})
        return value


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(
        style={"input_type": "password"}, required=True
    )
    re_new_password = serializers.CharField(
        style={"input_type": "password"}, required=True
    )

    def validate(self, data):
        if data["new_password"] != data["re_new_password"]:
            raise ValidationError("Passwords do not match.")
        return data




class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    