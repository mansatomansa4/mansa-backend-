"""
Celery Tasks for Mentorship Email Notifications

Async tasks for booking confirmations, reminders, and mentor notifications.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .supabase_client import supabase_client
from apps.users.models import User

logger = logging.getLogger(__name__)


def _get_users_for_booking(booking):
    """
    Resolve mentor and mentee Django User objects from a booking record.
    booking['mentee_id'] is a UUID referencing members(id), not Django user id.
    booking['mentor_id'] is a UUID referencing mentors(id).
    Returns (mentor_user, mentee_user, mentor_data) or raises.
    """
    # Get mentor data from mentors table
    mentor_data = supabase_client._client.table('mentors').select('*').eq(
        'id', booking['mentor_id']
    ).single().execute().data

    # Get mentee member record to find email
    mentee_member = supabase_client._client.table('members').select('email, name').eq(
        'id', booking['mentee_id']
    ).single().execute().data

    if not mentor_data or not mentee_member:
        return None, None, None

    # Look up mentor Django user by email (user_id may be NULL)
    mentor_user = None
    if mentor_data.get('user_id'):
        mentor_user = User.objects.filter(id=mentor_data['user_id']).first()
    if not mentor_user:
        # Fallback: find by member email linked to mentor
        mentor_member = supabase_client._client.table('members').select('email').eq(
            'id', mentor_data.get('member_id', '')
        ).maybeSingle().execute().data
        if mentor_member:
            mentor_user = User.objects.filter(email__iexact=mentor_member['email']).first()

    # Look up mentee Django user by email
    mentee_user = User.objects.filter(email__iexact=mentee_member['email']).first()

    return mentor_user, mentee_user, mentor_data


def _format_session_time(booking):
    """
    Format session_date (ISO timestamp) + duration_minutes into readable strings.
    Returns (date_str, time_str) e.g. ('January 27, 2026', '10:00 AM - 11:00 AM')
    """
    session_dt = datetime.fromisoformat(str(booking['session_date']).replace('Z', '+00:00'))
    date_str = session_dt.strftime('%B %d, %Y')
    start_str = session_dt.strftime('%I:%M %p')
    duration = booking.get('duration_minutes', 60)
    end_dt = session_dt + timedelta(minutes=int(duration))
    end_str = end_dt.strftime('%I:%M %p')
    time_str = f"{start_str} - {end_str}"
    return date_str, time_str


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_email(self, booking_id: str):
    """
    Send confirmation email to mentee after booking creation.
    """
    try:
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq(
            'id', booking_id
        ).single().execute().data

        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return

        mentor_user, mentee_user, mentor_data = _get_users_for_booking(booking)
        if not mentee_user:
            logger.error(f"Mentee user not found for booking {booking_id}")
            return

        date_str, time_str = _format_session_time(booking)
        mentor_name = f"{mentor_user.first_name} {mentor_user.last_name}".strip() if mentor_user else "Your Mentor"

        subject = f"Booking Request Submitted - {date_str}"
        message = f"""Hello {mentee_user.first_name},

Your mentorship session request has been submitted successfully!

Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}
- Status: Pending confirmation

{f"Meeting Link: {booking.get('meeting_url')}" if booking.get('meeting_url') else "Your mentor will share the meeting link once confirmed."}

{f"Notes: {booking.get('notes')}" if booking.get('notes') else ""}

Your mentor will review and confirm your session. You'll receive another email once confirmed.

You can manage this booking from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mentee_user.email],
            fail_silently=False,
        )

        logger.info(f"Booking confirmation email sent to {mentee_user.email} for booking {booking_id}")
        return True

    except Exception as exc:
        logger.error(f"Error sending booking confirmation email: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_mentor_booking_notification(self, booking_id: str):
    """
    Notify mentor about new booking request.
    """
    try:
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq(
            'id', booking_id
        ).single().execute().data

        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return

        mentor_user, mentee_user, mentor_data = _get_users_for_booking(booking)
        if not mentor_user:
            logger.error(f"Mentor user not found for booking {booking_id}")
            return

        date_str, time_str = _format_session_time(booking)
        mentee_name = f"{mentee_user.first_name} {mentee_user.last_name}".strip() if mentee_user else booking.get('mentee_name', 'A mentee')

        subject = f"New Mentorship Request - {date_str}"
        message = f"""Hello {mentor_user.first_name},

You have received a new mentorship session request!

Session Details:
- Mentee: {mentee_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Mentee Goals: {booking.get('mentee_goals')}" if booking.get('mentee_goals') else ""}
{f"Notes: {booking.get('notes')}" if booking.get('notes') else ""}

Please log in to your Mansa dashboard to confirm or manage this booking.

Best regards,
Mansa Mentorship Team
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mentor_user.email],
            fail_silently=False,
        )

        logger.info(f"Mentor notification email sent to {mentor_user.email} for booking {booking_id}")
        return True

    except Exception as exc:
        logger.error(f"Error sending mentor notification email: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_session_reminder_1h():
    """
    Celery Beat task - sends 1-hour reminders for upcoming sessions.
    Queries for confirmed bookings where session_date is within the next 60-90 minutes.
    """
    try:
        now = timezone.now()
        window_start = now + timedelta(minutes=55)
        window_end = now + timedelta(minutes=95)

        # Query confirmed bookings in the 1-hour window
        bookings = supabase_client._client.table('mentorship_bookings').select('*').eq(
            'status', 'confirmed'
        ).gte(
            'session_date', window_start.isoformat()
        ).lte(
            'session_date', window_end.isoformat()
        ).execute().data

        reminder_count = 0

        for booking in bookings:
            try:
                mentor_user, mentee_user, mentor_data = _get_users_for_booking(booking)
                if not mentee_user and not mentor_user:
                    continue

                date_str, time_str = _format_session_time(booking)
                meeting_link = booking.get('meeting_url') or ''

                # Send to mentee
                if mentee_user:
                    mentor_name = f"{mentor_user.first_name} {mentor_user.last_name}".strip() if mentor_user else "Your Mentor"
                    mentee_message = f"""Hello {mentee_user.first_name},

Your mentorship session is starting in about 1 hour!

Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Meeting Link: {meeting_link}" if meeting_link else "Your mentor will share the meeting link shortly."}

Please be ready and join on time.

Best regards,
Mansa Mentorship Team
"""
                    send_mail(
                        subject=f"Reminder: Session in 1 Hour - {date_str}",
                        message=mentee_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mentee_user.email],
                        fail_silently=True,
                    )

                # Send to mentor
                if mentor_user:
                    mentee_name = f"{mentee_user.first_name} {mentee_user.last_name}".strip() if mentee_user else "Your mentee"
                    mentor_message = f"""Hello {mentor_user.first_name},

Your mentorship session is starting in about 1 hour!

Session Details:
- Mentee: {mentee_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Meeting Link: {meeting_link}" if meeting_link else "Please share your meeting link with the mentee if you haven't already."}

Best regards,
Mansa Mentorship Team
"""
                    send_mail(
                        subject=f"Reminder: Session in 1 Hour - {date_str}",
                        message=mentor_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mentor_user.email],
                        fail_silently=True,
                    )

                reminder_count += 1

            except Exception as e:
                logger.error(f"Error sending 1h reminder for booking {booking['id']}: {e}")
                continue

        logger.info(f"Sent {reminder_count} one-hour session reminders")
        return reminder_count

    except Exception as e:
        logger.error(f"Error in send_session_reminder_1h task: {e}")
        return 0


@shared_task
def send_session_reminder_24h():
    """
    Celery Beat task - sends 24-hour reminders for upcoming sessions.
    Queries confirmed bookings where session_date is within the next 23-25 hours.
    """
    try:
        now = timezone.now()
        window_start = now + timedelta(hours=23)
        window_end = now + timedelta(hours=25)

        bookings = supabase_client._client.table('mentorship_bookings').select('*').eq(
            'status', 'confirmed'
        ).gte(
            'session_date', window_start.isoformat()
        ).lte(
            'session_date', window_end.isoformat()
        ).execute().data

        reminder_count = 0

        for booking in bookings:
            try:
                mentor_user, mentee_user, mentor_data = _get_users_for_booking(booking)
                if not mentee_user and not mentor_user:
                    continue

                date_str, time_str = _format_session_time(booking)
                meeting_link = booking.get('meeting_url') or ''

                # Send to mentee
                if mentee_user:
                    mentor_name = f"{mentor_user.first_name} {mentor_user.last_name}".strip() if mentor_user else "Your Mentor"
                    mentee_message = f"""Hello {mentee_user.first_name},

This is a reminder that your mentorship session is scheduled for tomorrow!

Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Meeting Link: {meeting_link}" if meeting_link else "Your mentor will share the meeting link before the session."}

We look forward to your session!

Best regards,
Mansa Mentorship Team
"""
                    send_mail(
                        subject=f"Reminder: Mentorship Session Tomorrow - {date_str}",
                        message=mentee_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mentee_user.email],
                        fail_silently=True,
                    )

                # Send to mentor
                if mentor_user:
                    mentee_name = f"{mentee_user.first_name} {mentee_user.last_name}".strip() if mentee_user else "Your mentee"
                    mentor_message = f"""Hello {mentor_user.first_name},

This is a reminder that you have a mentorship session scheduled for tomorrow!

Session Details:
- Mentee: {mentee_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Meeting Link: {meeting_link}" if meeting_link else "Please share your meeting link with the mentee."}

Best regards,
Mansa Mentorship Team
"""
                    send_mail(
                        subject=f"Reminder: Mentorship Session Tomorrow - {date_str}",
                        message=mentor_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mentor_user.email],
                        fail_silently=True,
                    )

                reminder_count += 1

            except Exception as e:
                logger.error(f"Error sending 24h reminder for booking {booking['id']}: {e}")
                continue

        logger.info(f"Sent {reminder_count} session reminders for tomorrow")
        return reminder_count

    except Exception as e:
        logger.error(f"Error in send_session_reminder_24h task: {e}")
        return 0


@shared_task
def send_booking_status_update_email(booking_id: str, old_status: str, new_status: str):
    """
    Send email when booking status changes (confirmed, cancelled, completed, etc.).
    Sends to the appropriate party (mentee, mentor, or both) based on the status change.
    """
    try:
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq(
            'id', booking_id
        ).single().execute().data

        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return

        mentor_user, mentee_user, mentor_data = _get_users_for_booking(booking)
        if not mentor_user and not mentee_user:
            logger.error(f"No users found for booking {booking_id}")
            return

        date_str, time_str = _format_session_time(booking)
        mentor_name = f"{mentor_user.first_name} {mentor_user.last_name}".strip() if mentor_user else "Your Mentor"
        mentee_name = f"{mentee_user.first_name} {mentee_user.last_name}".strip() if mentee_user else "A mentee"

        # --- CONFIRMED ---
        if new_status == 'confirmed' and mentee_user:
            message = f"""Hello {mentee_user.first_name},

Great news! Your mentorship session has been CONFIRMED by {mentor_name}!

Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Meeting Link: {booking.get('meeting_url')}" if booking.get('meeting_url') else "Your mentor will share the meeting link before the session."}

What to do next:
- Add this session to your calendar
- Prepare any questions or topics you'd like to discuss
- Join the meeting on time

You can view and manage your bookings from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Session Confirmed with {mentor_name} - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee_user.email],
                fail_silently=False,
            )
            logger.info(f"Confirmation email sent to mentee {mentee_user.email}")
            return True

        # --- CANCELLED BY MENTOR ---
        elif new_status == 'cancelled_by_mentor' and mentee_user:
            message = f"""Hello {mentee_user.first_name},

Unfortunately, your mentorship session has been cancelled by {mentor_name}.

Cancelled Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

We apologize for the inconvenience. You can browse other available mentors and book a new session from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Session Cancelled - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee_user.email],
                fail_silently=False,
            )
            logger.info(f"Cancellation email sent to mentee {mentee_user.email}")
            return True

        # --- CANCELLED BY MENTEE ---
        elif new_status == 'cancelled_by_mentee' and mentor_user:
            message = f"""Hello {mentor_user.first_name},

A mentorship session has been cancelled by the mentee.

Cancelled Session Details:
- Mentee: {mentee_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

Your time slot is now available for other bookings.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Session Cancelled by Mentee - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentor_user.email],
                fail_silently=False,
            )
            logger.info(f"Cancellation email sent to mentor {mentor_user.email}")
            return True

        # --- COMPLETED ---
        elif new_status == 'completed' and mentee_user:
            message = f"""Hello {mentee_user.first_name},

Thank you for completing your mentorship session!

Completed Session:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}

We'd love to hear your feedback! Please take a moment to rate your session and leave a review for your mentor from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Session Completed - Thank You! - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee_user.email],
                fail_silently=False,
            )
            logger.info(f"Completion email sent to mentee {mentee_user.email}")
            return True

        # --- REJECTED ---
        elif new_status == 'rejected' and mentee_user:
            message = f"""Hello {mentee_user.first_name},

Unfortunately, your mentorship session request has been declined by {mentor_name}.

Declined Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

Don't be discouraged! You can browse other available mentors and book a new session from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Session Request Declined - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee_user.email],
                fail_silently=False,
            )
            logger.info(f"Rejection email sent to mentee {mentee_user.email}")
            return True

        # --- RESCHEDULED (notify both) ---
        elif new_status == 'rescheduled':
            if mentee_user:
                message = f"""Hello {mentee_user.first_name},

Your mentorship session has been rescheduled.

New Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- New Date: {date_str}
- New Time: {time_str}

Please update your calendar with the new date and time.

Best regards,
Mansa Mentorship Team
"""
                send_mail(
                    subject=f"Session Rescheduled - {date_str}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentee_user.email],
                    fail_silently=False,
                )

            if mentor_user:
                message = f"""Hello {mentor_user.first_name},

A mentorship session has been rescheduled.

New Session Details:
- Mentee: {mentee_name}
- Topic: {booking.get('topic', 'N/A')}
- New Date: {date_str}
- New Time: {time_str}

Please update your calendar with the new date and time.

Best regards,
Mansa Mentorship Team
"""
                send_mail(
                    subject=f"Session Rescheduled - {date_str}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentor_user.email],
                    fail_silently=False,
                )

            logger.info(f"Reschedule email sent for booking {booking_id}")
            return True

        # --- NO SHOW ---
        elif new_status == 'no_show' and mentee_user:
            message = f"""Hello {mentee_user.first_name},

You have been marked as a no-show for your scheduled mentorship session.

Session Details:
- Mentor: {mentor_name}
- Topic: {booking.get('topic', 'N/A')}
- Date: {date_str}
- Time: {time_str}

If this was a mistake, please contact the mentor or reach out to support.

Best regards,
Mansa Mentorship Team
"""
            send_mail(
                subject=f"Missed Session - {date_str}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee_user.email],
                fail_silently=False,
            )
            logger.info(f"No-show email sent for booking {booking_id}")
            return True

        logger.info(f"Status update processed for booking {booking_id}: {old_status} -> {new_status}")
        return True

    except Exception as e:
        logger.error(f"Error sending status update email: {e}")
        return False
