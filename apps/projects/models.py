from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Project(models.Model):
    PROJECT_STATUS = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("closed", "Closed"),
        ("archived", "Archived"),
    ]
    APPROVAL_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)

    admission_start_date = models.DateTimeField()
    admission_end_date = models.DateTimeField()

    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default="draft")
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default="pending")

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects")
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_projects"
    )

    max_participants = models.IntegerField(default=100)
    current_participants = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def is_admission_open(self) -> bool:
        now = timezone.now()
        return self.admission_start_date <= now <= self.admission_end_date

    def days_until_admission_opens(self) -> int:
        if self.admission_start_date > timezone.now():
            return (self.admission_start_date - timezone.now()).days
        return 0

    def days_until_admission_closes(self) -> int:
        if self.admission_end_date > timezone.now():
            return (self.admission_end_date - timezone.now()).days
        return 0


class ProjectApplication(models.Model):
    APPLICATION_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("waitlist", "Waitlisted"),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="applications")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_applications"
    )
    application_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ["project", "user"]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"Application: {self.user} -> {self.project}"
