from django.conf import settings
from rest_framework import serializers

from . import models


class ProjectSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Project
        fields = "__all__"

    def get_image_url(self, obj):
        """Convert relative image path to full Supabase storage URL"""
        if not obj.image_url:
            return None

        # If already a full URL, return as-is
        if obj.image_url.startswith('http'):
            return obj.image_url

        # Construct full Supabase storage URL for public bucket
        project_ref = 'adnteftmqytcnieqmlma'
        bucket_name = 'project-images'

        # Remove leading slash if present
        image_path = obj.image_url.lstrip('/')

        # Public bucket URL format
        return f"https://{project_ref}.supabase.co/storage/v1/object/public/{bucket_name}/{image_path}"


class ProjectApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectApplication
        fields = "__all__"
        read_only_fields = ["status", "applied_date", "created_at", "updated_at"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'updated_at']  # UUID and timestamps are auto-generated


class CommunityMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CommunityMember
        fields = "__all__"


class ResearchCohortApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Research Cohort Applications"""

    class Meta:
        model = models.ResearchCohortApplication
        fields = "__all__"
        read_only_fields = [
            "id",
            "member_id",
            "status",
            "applied_at",
            "reviewed_at",
            "reviewed_by",
            "reviewer_notes",
            "created_at",
            "updated_at",
        ]


class ResearchCohortApplicationCreateSerializer(serializers.Serializer):
    """Serializer for creating Research Cohort Applications with email verification"""

    # Required fields
    email = serializers.EmailField()
    research_interest = serializers.CharField()
    motivation = serializers.CharField()

    # Optional fields
    research_topic = serializers.CharField(required=False, allow_blank=True)
    research_experience = serializers.CharField(required=False, allow_blank=True)
    academic_background = serializers.CharField(required=False, allow_blank=True)
    current_institution = serializers.CharField(required=False, allow_blank=True)
    highest_qualification = serializers.CharField(required=False, allow_blank=True)
    field_of_study = serializers.CharField(required=False, allow_blank=True)
    publications = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)
    availability = serializers.CharField(required=False, allow_blank=True)
    preferred_research_area = serializers.CharField(required=False, allow_blank=True)
    cohort_batch = serializers.CharField(required=False, allow_blank=True)


class EducationCohortApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Education Cohort Applications"""

    class Meta:
        model = models.EducationCohortApplication
        fields = "__all__"
        read_only_fields = [
            "id",
            "member_id",
            "status",
            "applied_at",
            "reviewed_at",
            "reviewed_by",
            "reviewer_notes",
            "created_at",
            "updated_at",
        ]


class EducationCohortApplicationCreateSerializer(serializers.Serializer):
    """Serializer for creating Education Cohort Applications with email verification"""

    # Required fields
    email = serializers.EmailField()
    education_interest = serializers.CharField()
    motivation = serializers.CharField()

    # Optional fields
    current_education_level = serializers.CharField(required=False, allow_blank=True)
    target_education_level = serializers.CharField(required=False, allow_blank=True)
    current_institution = serializers.CharField(required=False, allow_blank=True)
    field_of_study = serializers.CharField(required=False, allow_blank=True)
    learning_goals = serializers.CharField(required=False, allow_blank=True)
    skills_to_develop = serializers.CharField(required=False, allow_blank=True)
    prior_experience = serializers.CharField(required=False, allow_blank=True)
    preferred_learning_format = serializers.CharField(required=False, allow_blank=True)
    time_commitment = serializers.CharField(required=False, allow_blank=True)
    availability = serializers.CharField(required=False, allow_blank=True)
    cohort_batch = serializers.CharField(required=False, allow_blank=True)
