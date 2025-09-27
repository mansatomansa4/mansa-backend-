from django.utils import timezone
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.emails.tasks import send_user_approval_email, send_user_denial_email

from .models import User
from .permissions import IsAdmin
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


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
