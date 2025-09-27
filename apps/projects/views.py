from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsAdmin, IsApprovedUser

from .models import Project, ProjectApplication
from .serializers import ProjectApplicationSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):  # type: ignore
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        if self.action in ["apply"]:
            return [IsApprovedUser()]
        # create/update/delete & admin actions
        return [IsAdmin()]

    def perform_create(self, serializer):  # type: ignore
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        project = self.get_object()
        user = request.user
        if not project.is_admission_open():
            return Response({"detail": "Admission is not currently open"}, status=400)
        if ProjectApplication.objects.filter(project=project, user=user).exists():
            return Response({"detail": "Already applied"}, status=400)
        if project.current_participants >= project.max_participants:
            return Response({"detail": "Project is full"}, status=400)
        application = ProjectApplication.objects.create(
            project=project, user=user, application_data=request.data
        )
        return Response(ProjectApplicationSerializer(application).data, status=201)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        project = self.get_object()
        if project.approval_status == "approved":
            return Response({"detail": "Already approved"}, status=400)
        project.approval_status = "approved"
        project.approved_by = request.user
        project.status = "active"
        project.save(update_fields=["approval_status", "approved_by", "status"])
        return Response({"detail": "Project approved"})

    @action(detail=True, methods=["post"])
    def deny(self, request, pk=None):
        project = self.get_object()
        if project.approval_status == "denied":
            return Response({"detail": "Already denied"}, status=400)
        project.approval_status = "denied"
        project.status = "archived"
        project.save(update_fields=["approval_status", "status"])
        return Response({"detail": "Project denied"})

    @action(detail=True, methods=["get"], permission_classes=[IsAdmin])
    def applications(self, request, pk=None):
        project = self.get_object()
        qs = project.applications.select_related("user").all()
        return Response(ProjectApplicationSerializer(qs, many=True).data)


class ProjectApplicationAdminViewSet(viewsets.ModelViewSet):
    queryset = ProjectApplication.objects.select_related("project", "user").all()
    serializer_class = ProjectApplicationSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "patch", "delete"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        app = self.get_object()
        if app.status == "approved":
            return Response({"detail": "Already approved"}, status=400)
        app.status = "approved"
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response({"detail": "Application approved"})

    @action(detail=True, methods=["post"])
    def deny(self, request, pk=None):
        app = self.get_object()
        if app.status == "denied":
            return Response({"detail": "Already denied"}, status=400)
        app.status = "denied"
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        return Response({"detail": "Application denied"})
