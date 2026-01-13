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
    Passwordless login using email only.
    Checks if email exists in Supabase database and returns JWT token + user info.
    """
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response(
            {"error": "Email is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Django is now connected directly to Supabase PostgreSQL
        user = User.objects.get(email=email)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Return user info with tokens
        return Response({
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
            }
        })
        
    except User.DoesNotExist:
        logger.warning(f"Login attempt with unregistered email: {email}")
        return Response(
            {
                "error": "Email not found in database",
                "detail": "This email is not registered. Please contact admin or register first."
            },
            status=status.HTTP_404_NOT_FOUND
        )
