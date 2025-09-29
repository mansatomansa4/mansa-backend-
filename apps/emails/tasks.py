from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailCampaign, EmailLog, EmailTemplate

User = get_user_model()


def _render_subject(template: EmailTemplate, context: dict) -> str:
    return template.subject.format(**context)


def _render_text(template: EmailTemplate, context: dict) -> str:
    return template.text_content.format(**context) if template.text_content else ""


def _render_html(template: EmailTemplate, context: dict) -> str:
    # Simple placeholder; could integrate Django templates.
    return template.html_content.format(**context)


@shared_task
def send_user_approval_email(user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:  # pragma: no cover - defensive
        return
    template = EmailTemplate.objects.filter(template_type="approval", is_active=True).first()
    if not template:
        return
    context = {"user_email": user.email, "first_name": user.first_name}
    subject = _render_subject(template, context)
    text_body = _render_text(template, context)
    html_body = _render_html(template, context)
    send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_body)
    EmailLog.objects.create(
        recipient=user,
        template=template,
        subject=subject,
        status="sent",
        sent_at=timezone.now(),
    )


@shared_task
def send_welcome_email(user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    template = EmailTemplate.objects.filter(template_type="welcome", is_active=True).first()
    if not template:
        subject = "Welcome to Mansa Platform!"
        text_body = f"""Hello {user.first_name or user.email},

Welcome to the Mansa platform! We're excited to have you join our community.

Our platform helps connect innovators, entrepreneurs, and creators to build amazing projects together.

Join our community WhatsApp group to connect with other members:
https://chat.whatsapp.com/ERMH6rdc1h52aTL6eib793

If you have any questions, feel free to reach out to our support team.

Best regards,
The Mansa Team"""

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Welcome to Mansa Platform!</h2>

        <p>Hello <strong>{user.first_name or user.email}</strong>,</p>

        <p>Welcome to the Mansa platform! We're excited to have you join our community.</p>

        <p>Our platform helps connect innovators, entrepreneurs, and creators to build amazing projects together.</p>

        <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #007bff;">Join Our Community</h3>
            <p>Connect with other members in our WhatsApp group:</p>
            <a href="https://chat.whatsapp.com/ERMH6rdc1h52aTL6eib793"
               style="background-color: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
               Join WhatsApp Group
            </a>
        </div>

        <p>If you have any questions, feel free to reach out to our support team.</p>

        <p style="margin-top: 30px;">
            Best regards,<br>
            <strong>The Mansa Team</strong>
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #666;">
            This email was sent to {user.email}. You're receiving this because you signed up for the Mansa platform.
        </p>
    </div>
</body>
</html>"""

        send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_body)
        EmailLog.objects.create(
            recipient=user,
            subject=subject,
            status="sent",
            sent_at=timezone.now(),
        )
    else:
        context = {"user_email": user.email, "first_name": user.first_name or user.email}
        subject = _render_subject(template, context)
        text_body = _render_text(template, context)
        html_body = _render_html(template, context)
        send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_body)
        EmailLog.objects.create(
            recipient=user,
            template=template,
            subject=subject,
            status="sent",
            sent_at=timezone.now(),
        )


@shared_task
def send_user_denial_email(user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:  # pragma: no cover
        return
    template = EmailTemplate.objects.filter(template_type="denial", is_active=True).first()
    if not template:
        return
    context = {"user_email": user.email, "first_name": user.first_name}
    subject = _render_subject(template, context)
    text_body = _render_text(template, context)
    html_body = _render_html(template, context)
    send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_body)
    EmailLog.objects.create(
        recipient=user,
        template=template,
        subject=subject,
        status="sent",
        sent_at=timezone.now(),
    )


@shared_task
def send_campaign_emails(campaign_id: int):
    try:
        campaign = EmailCampaign.objects.select_related("template").get(id=campaign_id)
    except EmailCampaign.DoesNotExist:  # pragma: no cover
        return
    template = campaign.template

    # Build recipient queryset
    qs = User.objects.none()
    if campaign.target_all_users:
        qs = User.objects.all()
    else:
        if campaign.target_approved_users:
            qs = qs.union(User.objects.filter(approval_status="approved"))
        if campaign.target_pending_users:
            qs = qs.union(User.objects.filter(approval_status="pending"))
        if campaign.specific_users.exists():
            qs = qs.union(campaign.specific_users.all())

    recipients = list(qs.distinct())

    sent_count = 0
    for user in recipients:
        context = {"user_email": user.email, "first_name": user.first_name}
        subject = _render_subject(template, context)
        text_body = _render_text(template, context)
        html_body = _render_html(template, context)
        try:
            send_mail(
                subject,
                text_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_body,
            )
            EmailLog.objects.create(
                recipient=user,
                campaign=campaign,
                template=template,
                subject=subject,
                status="sent",
                sent_at=timezone.now(),
            )
            sent_count += 1
        except Exception as exc:  # pragma: no cover - defensive
            EmailLog.objects.create(
                recipient=user,
                campaign=campaign,
                template=template,
                subject=subject,
                status="failed",
                error_message=str(exc),
            )

    campaign.status = "sent"
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=["status", "sent_at"])
    return sent_count
