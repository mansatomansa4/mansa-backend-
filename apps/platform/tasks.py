from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_applicant_email(applicant_email, applicant_name, subject, message):
    """
    Send email to a project applicant
    """
    try:
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a202c; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f7fafc; }}
                .footer {{ text-align: center; padding: 20px; color: #718096; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Mansa</h1>
                </div>
                <div class="content">
                    <p>Dear {applicant_name},</p>
                    <div>{message}</div>
                </div>
                <div class="footer">
                    <p>This email was sent from Mansa Admin Dashboard</p>
                    <p>&copy; 2024 Mansa. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=message,  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[applicant_email],
            html_message=html_message,
            fail_silently=False,
        )

        return f"Email sent successfully to {applicant_email}"

    except Exception as e:
        return f"Failed to send email to {applicant_email}: {str(e)}"


@shared_task
def send_bulk_applicant_emails(applicant_emails, subject, message):
    """
    Send bulk emails to multiple applicants
    """
    sent_count = 0
    failed_count = 0

    for email_data in applicant_emails:
        try:
            send_applicant_email.delay(
                applicant_email=email_data['email'],
                applicant_name=email_data['name'],
                subject=subject,
                message=message
            )
            sent_count += 1
        except Exception:
            failed_count += 1

    return f"Queued {sent_count} emails, {failed_count} failed"
