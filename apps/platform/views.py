from django.db import connection
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CommunityMember, Member, Project, ProjectApplication
from .serializers import (
    CommunityMemberSerializer,
    MemberSerializer,
    ProjectApplicationSerializer,
    ProjectSerializer,
)


class DatabaseGuardMixin:
    """Return 503 if we are not on Postgres (e.g., local sqlite dev)."""

    def _db_is_sqlite(self) -> bool:
        return "sqlite" in connection.vendor

    def list(self, request, *args, **kwargs):  # type: ignore
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):  # type: ignore
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)
        return super().retrieve(request, *args, **kwargs)


class ProjectViewSet(DatabaseGuardMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all().order_by("-created_at")
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    filterset_fields = {
        "status": ["exact", "in"],
        "project_type": ["exact", "in"],
    }
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]


class MemberViewSet(DatabaseGuardMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Member.objects.all().order_by("-created_at")
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]


class CommunityMemberViewSet(DatabaseGuardMixin, viewsets.ReadOnlyModelViewSet):
    queryset = CommunityMember.objects.all().order_by("-created_at")
    serializer_class = CommunityMemberSerializer
    permission_classes = [IsAuthenticated]


class ProjectApplicationViewSet(
    DatabaseGuardMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ProjectApplication.objects.all().order_by("-applied_date")
    serializer_class = ProjectApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):  # type: ignore
        # Auto-set applicant fields if not provided
        user = self.request.user
        data = {
            "applicant_name": getattr(user, "first_name", "") or "Anonymous",
            "applicant_email": getattr(user, "email", ""),
        }
        for k, v in data.items():
            if k not in serializer.validated_data or not serializer.validated_data.get(k):
                serializer.validated_data[k] = v
        serializer.save()
