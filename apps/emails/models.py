from __future__ import annotations

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class EmailTemplate(models.Model):
    TEMPLATE_TYPES = [
        ("welcome", "Welcome Email"),
        ("approval", "User Approval"),
        ("denial", "User Denial"),
        ("project_approval", "Project Approval"),
        ("project_denial", "Project Denial"),
        ("campaign", "Email Campaign"),
        ("notification", "Notification"),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_email_templates"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class EmailCampaign(models.Model):
    CAMPAIGN_STATUS = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("sending", "Sending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    name = models.CharField(max_length=100)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name="campaigns")
    target_all_users = models.BooleanField(default=False)
    target_approved_users = models.BooleanField(default=False)
    target_pending_users = models.BooleanField(default=False)
    specific_users = models.ManyToManyField(User, blank=True, related_name="targeted_campaigns")
    scheduled_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_campaigns")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Campaign: {self.name}"


class EmailLog(models.Model):
    EMAIL_STATUS = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
        ("opened", "Opened"),
        ("clicked", "Clicked"),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_logs")
    campaign = models.ForeignKey(
        EmailCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    template = models.ForeignKey(
        EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=EMAIL_STATUS, default="queued")
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EmailLog: {self.recipient} {self.subject} ({self.status})"
