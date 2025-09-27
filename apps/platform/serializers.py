from rest_framework import serializers

from . import models


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = "__all__"


class ProjectApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectApplication
        fields = "__all__"
        read_only_fields = ["status", "applied_date", "created_at", "updated_at"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        fields = "__all__"


class CommunityMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CommunityMember
        fields = "__all__"
