from __future__ import annotations

from django.db import models

# NOTE: These models mirror existing Supabase Postgres tables.
# They are declared with managed = False so Django will not create/alter them.
# Keep field names aligned with the remote schema. Add indexes in SQL if needed.


class Admin(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, default="admin")
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "admins"
        managed = False
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    def __str__(self):
        return self.email


class AdminAuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(
        Admin,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_column="admin_id",
    )
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=255, null=True, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "admin_audit_log"
        managed = False
        verbose_name = "Admin Audit Log"
        verbose_name_plural = "Admin Audit Logs"


class Member(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    country = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    linkedin = models.TextField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    areaOfExpertise = models.TextField(null=True, blank=True)
    school = models.TextField(null=True, blank=True)
    level = models.TextField(null=True, blank=True)
    occupation = models.TextField(null=True, blank=True)
    jobtitle = models.TextField(null=True, blank=True)
    industry = models.TextField(null=True, blank=True)
    major = models.TextField(null=True, blank=True)
    gender = models.TextField()
    membershiptype = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "members"
        managed = False
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def __str__(self):
        return f"{self.name} <{self.email}>"


class CommunityMember(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.TextField()
    email = models.TextField(unique=True)
    phone = models.TextField(null=True, blank=True)
    joined_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    profile_picture = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    motivation = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "community_members"
        managed = False
        verbose_name = "Community Member"
        verbose_name_plural = "Community Members"


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    launch_date = models.DateField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)
    project_type = models.TextField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    participants_count = models.IntegerField(null=True, blank=True)
    max_participants = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    member_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "projects"
        managed = False
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    id = models.UUIDField(primary_key=True)
    project_id = models.IntegerField()
    member_email = models.TextField()
    member_name = models.TextField()
    role = models.TextField(null=True, blank=True)
    joined_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    contribution_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    member_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "project_members"
        managed = False
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"


class ProjectApplication(models.Model):
    id = models.UUIDField(primary_key=True)
    project_id = models.IntegerField()
    applicant_name = models.TextField()
    applicant_email = models.TextField()
    skills = models.TextField(null=True, blank=True)
    motivation = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    applied_date = models.DateTimeField(null=True, blank=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    member_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "project_applications"
        managed = False
        verbose_name = "Project Application"
        verbose_name_plural = "Project Applications"


class EmailNotification(models.Model):
    id = models.AutoField(primary_key=True)
    recipient_email = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=255, null=True, blank=True)
    email_type = models.CharField(max_length=255)
    subject = models.TextField()
    template_used = models.CharField(max_length=255, null=True, blank=True)
    sent_by = models.IntegerField(null=True, blank=True)
    application_id = models.UUIDField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "email_notifications"
        managed = False
        verbose_name = "Email Notification"
        verbose_name_plural = "Email Notifications"
