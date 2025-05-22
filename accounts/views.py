from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics

from rest_framework_simplejwt.tokens import (
    RefreshToken,
)


from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.db import transaction


from InventoryManagement.utils.context_manager import set_current_context
from InventoryManagement.utils.crudevents import create_crudevent
from accounts.serializers import (
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    UserDataSerializer,
)


User = get_user_model()


class UserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDataSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access

    def get_object(self):
        return self.request.user  # Return the currently authenticated user

    def put(self, request, *args, **kwargs):
        # Customize PUT behavior if needed (e.g., partial updates)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )  # Set partial=True for PATCH
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response(
                {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access this view
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User with this email does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            # Construct the reset link. Be sure to configure your frontend URL.
            reset_link = f"{settings.FRONTEND_URL}authentication/password-reset?uid={uidb64}&token={token}"  # Use settings

            try:
                send_mail(
                    subject="Password Reset Request",
                    message=f"Please click the link below to reset your password:\n{reset_link}",
                    from_email=settings.EMAIL_HOST_USER,  # Use settings
                    recipient_list=[email],
                    fail_silently=False,  # Set to true in production once you've tested
                )
                return Response(
                    {"detail": "Password reset email sent."}, status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]
            uidb64 = serializer.validated_data["uid"]
            # uidb64 = request.data.get('uid') # Get uid from request data
            new_password = serializer.validated_data["new_password"]

            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (ValueError, User.DoesNotExist):
                return Response(
                    {"detail": "Invalid reset link."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response(
                    {"detail": "Password reset successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "Invalid reset link."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @transaction.atomic
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]

        try:
            with set_current_context(self.request.user):
                with transaction.atomic():
                    token = RefreshToken(refresh_token)
                    blacklisted_token, _ = token.blacklist()
                    create_crudevent(obj=blacklisted_token)

            return Response(
                {"message": "User successfully logged out"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
