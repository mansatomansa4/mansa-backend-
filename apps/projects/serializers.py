from rest_framework import serializers

from .models import Project, ProjectApplication


class ProjectSerializer(serializers.ModelSerializer):
    is_admission_open = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "detailed_description",
            "image",
            "admission_start_date",
            "admission_end_date",
            "status",
            "approval_status",
            "max_participants",
            "current_participants",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
            "is_admission_open",
        ]
        read_only_fields = [
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
            "current_participants",
        ]

    def get_is_admission_open(self, obj):  # pragma: no cover - simple passthrough
        return obj.is_admission_open()


class ProjectApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectApplication
        fields = [
            "id",
            "project",
            "user",
            "application_data",
            "status",
            "reviewed_by",
            "review_notes",
            "applied_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "status",
            "reviewed_by",
            "review_notes",
            "applied_at",
            "reviewed_at",
            "user",
        ]
