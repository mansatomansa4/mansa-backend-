from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.emails.models import EmailCampaign, EmailLog
from apps.projects.models import Project, ProjectApplication
from apps.users.models import User


def overview_metrics():
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    return {
        "users_total": User.objects.count(),
        "users_approved": User.objects.filter(approval_status="approved").count(),
        "projects_total": Project.objects.count(),
        "projects_active": Project.objects.filter(status="active").count(),
        "applications_total": ProjectApplication.objects.count(),
        "emails_sent_24h": EmailLog.objects.filter(sent_at__gte=day_ago, status="sent").count(),
    }


def user_metrics():
    return {
        "by_approval": dict(User.objects.values_list("approval_status").annotate(c=Count("id"))),
        "by_role": dict(User.objects.values_list("role").annotate(c=Count("id"))),
    }


def project_metrics():
    return {
        "by_status": dict(Project.objects.values_list("status").annotate(c=Count("id"))),
        "by_approval_status": dict(
            Project.objects.values_list("approval_status").annotate(c=Count("id"))
        ),
    }


def email_metrics():
    return {
        "campaigns_total": EmailCampaign.objects.count(),
        "logs_sent": EmailLog.objects.filter(status="sent").count(),
        "logs_failed": EmailLog.objects.filter(status="failed").count(),
    }
