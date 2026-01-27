from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import logging

logger = logging.getLogger(__name__)

from apps.emails.tasks import send_user_approval_email, send_user_denial_email, send_welcome_email

from .models import User
from .permissions import IsAdmin
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that uses email instead of username."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_welcome_email.delay(user.id)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "patch", "delete"]

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin])
    def pending(self, request):
        qs = self.get_queryset().filter(approval_status="pending")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        user = self.get_object()
        if user.approval_status == "approved":
            return Response({"detail": "Already approved"}, status=400)
        user.approval_status = "approved"
        user.date_approved = timezone.now()
        user.approved_by = request.user
        user.save(update_fields=["approval_status", "date_approved", "approved_by"])
        send_user_approval_email.delay(user.id)
        return Response({"detail": "User approved"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def deny(self, request, pk=None):
        user = self.get_object()
        if user.approval_status == "denied":
            return Response({"detail": "Already denied"}, status=400)
        user.approval_status = "denied"
        user.save(update_fields=["approval_status"])
        send_user_denial_email.delay(user.id)
        return Response({"detail": "User denied"})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def email_login(request):
    """
    Login using email and password.
    Checks if email exists in members table, auto-creates user with default password if needed.
    Returns JWT token. Includes must_change_password flag so frontend can prompt password change.
    Also auto-creates mentor profile in Supabase for mentor users.
    """
    from apps.platform.models import Member
    from apps.mentorship.supabase_client import supabase_client

    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '').strip()

    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not password:
        return Response(
            {"error": "Password is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # First, try to get existing user
        user = User.objects.get(email=email)

    except User.DoesNotExist:
        # User doesn't exist in users_user table, check members table
        try:
            member = Member.objects.get(email__iexact=email)
            logger.info(f"Member found in members table: {email}. Auto-creating user account.")

            # Parse member name into first_name and last_name
            name_parts = member.name.strip().split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Determine mentor/mentee status from membershiptype
            membershiptype = (member.membershiptype or "").lower()
            is_mentor = 'mentor' in membershiptype
            is_mentee = 'mentee' in membershiptype or membershiptype == 'student'

            # If neither, default to mentee
            if not is_mentor and not is_mentee:
                is_mentee = True

            # Set role based on membershiptype
            if is_mentor and is_mentee:
                role = 'mentor_mentee'
            elif is_mentor:
                role = 'mentor'
            else:
                role = 'mentee'

            # Auto-create user from member data with default password
            user = User.objects.create_user(
                email=email,
                password=User.DEFAULT_PASSWORD,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_mentor=is_mentor,
                is_mentee=is_mentee,
                approval_status='approved',  # Auto-approve members
                must_change_password=True,
            )
            logger.info(f"Auto-created user account for member: {email} (role: {role})")

        except Member.DoesNotExist:
            # Email not found in either table
            logger.warning(f"Login attempt with unregistered email: {email}")
            return Response(
                {
                    "error": "Email not found in database",
                    "detail": "This email is not registered in the Mansa community. Please contact admin."
                },
                status=status.HTTP_404_NOT_FOUND
            )

    # Verify password
    if not user.check_password(password):
        return Response(
            {"error": "Invalid password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Auto-create mentor profile in Supabase if user is a mentor
    mentor_profile = None
    if user.is_mentor:
        try:
            # Check if mentor profile already exists
            existing_mentor = supabase_client.get_mentor_by_user_id(user.id)
            if not existing_mentor:
                # Try to sync/create mentor profile from member data
                mentor_profile = supabase_client.sync_mentor_from_member(email, user.id)
                if mentor_profile:
                    logger.info(f"Auto-created mentor profile in Supabase for user: {email}")
                else:
                    logger.warning(f"Could not auto-create mentor profile for user: {email}")
            else:
                mentor_profile = existing_mentor
                logger.info(f"Mentor profile already exists for user: {email}")
        except Exception as e:
            logger.error(f"Error auto-creating mentor profile for {email}: {e}")
            # Don't fail login if mentor profile creation fails

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Return user info with tokens
    response_data = {
        "access": access_token,
        "refresh": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_mentor": user.is_mentor,
            "is_mentee": user.is_mentee,
            "approval_status": user.approval_status,
            "must_change_password": user.must_change_password,
        }
    }

    # Include mentor_id if available
    if mentor_profile:
        response_data["user"]["mentor_id"] = mentor_profile.get("id")

    return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password. Requires current_password and new_password.
    Clears must_change_password flag after successful change.
    """
    current_password = request.data.get('current_password', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not current_password or not new_password:
        return Response(
            {"error": "Both current_password and new_password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user
    if not user.check_password(current_password):
        return Response(
            {"error": "Current password is incorrect"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if current_password == new_password:
        return Response(
            {"error": "New password must be different from current password"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])

    # Generate new tokens since password changed
    refresh = RefreshToken.for_user(user)
    return Response({
        "detail": "Password changed successfully",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })
