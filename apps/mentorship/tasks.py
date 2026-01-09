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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_email(self, booking_id: str):
    """
    Send confirmation email to mentee after booking creation.
    Includes mentor details and session information.
    """
    try:
        # Fetch booking details
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq('id', booking_id).single().execute().data
        
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return
        
        # Fetch mentor and mentee details
        mentor_data = supabase_client._client.table('mentors').select('*').eq('id', booking['mentor_id']).single().execute().data
        mentee = User.objects.filter(id=booking['mentee_id']).first()
        mentor_user = User.objects.filter(id=mentor_data['user_id']).first()
        
        if not mentee or not mentor_user:
            logger.error(f"User data not found for booking {booking_id}")
            return
        
        # Format session details
        session_date = datetime.fromisoformat(booking['session_date']).strftime('%B %d, %Y')
        start_time = datetime.fromisoformat(booking['start_time']).strftime('%I:%M %p')
        end_time = datetime.fromisoformat(booking['end_time']).strftime('%I:%M %p')
        
        # Email content
        subject = f"Mentorship Session Confirmed - {session_date}"
        message = f"""
Hello {mentee.first_name},

Your mentorship session has been confirmed!

Session Details:
- Mentor: {mentor_user.first_name} {mentor_user.last_name}
- Topic: {booking['topic']}
- Date: {session_date}
- Time: {start_time} - {end_time}
- Status: {booking['status'].replace('_', ' ').title()}

{f"Meeting Link: {booking['meeting_link']}" if booking.get('meeting_link') else "Your mentor will share the meeting link before the session."}

{f"Additional Notes:\\n{booking['description']}" if booking.get('description') else ""}

You can manage this booking from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mentee.email],
            fail_silently=False,
        )
        
        logger.info(f"Booking confirmation email sent to {mentee.email} for booking {booking_id}")
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
        # Fetch booking details
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq('id', booking_id).single().execute().data
        
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return
        
        # Fetch mentor and mentee details
        mentor_data = supabase_client._client.table('mentors').select('*').eq('id', booking['mentor_id']).single().execute().data
        mentee = User.objects.filter(id=booking['mentee_id']).first()
        mentor_user = User.objects.filter(id=mentor_data['user_id']).first()
        
        if not mentee or not mentor_user:
            logger.error(f"User data not found for booking {booking_id}")
            return
        
        # Format session details
        session_date = datetime.fromisoformat(booking['session_date']).strftime('%B %d, %Y')
        start_time = datetime.fromisoformat(booking['start_time']).strftime('%I:%M %p')
        end_time = datetime.fromisoformat(booking['end_time']).strftime('%I:%M %p')
        
        # Email content
        subject = f"New Mentorship Request - {session_date}"
        message = f"""
Hello {mentor_user.first_name},

You have received a new mentorship session request!

Session Details:
- Mentee: {mentee.first_name} {mentee.last_name}
- Topic: {booking['topic']}
- Date: {session_date}
- Time: {start_time} - {end_time}

{f"Mentee Message:\\n{booking['description']}" if booking.get('description') else ""}

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
def send_session_reminder_24h():
    """
    Celery Beat task - runs daily to send 24-hour reminders.
    Sends reminder for all confirmed sessions happening in 24 hours.
    """
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        tomorrow_date = tomorrow.date()
        
        # Fetch confirmed bookings for tomorrow
        bookings = supabase_client._client.table('mentorship_bookings').select('*').eq('session_date', str(tomorrow_date)).eq('status', 'confirmed').execute().data
        
        reminder_count = 0
        
        for booking in bookings:
            try:
                # Fetch users
                mentor_data = supabase_client._client.table('mentors').select('*').eq('id', booking['mentor_id']).single().execute().data
                mentee = User.objects.filter(id=booking['mentee_id']).first()
                mentor_user = User.objects.filter(id=mentor_data['user_id']).first()
                
                if not mentee or not mentor_user:
                    continue
                
                # Format session details
                session_date = datetime.fromisoformat(booking['session_date']).strftime('%B %d, %Y')
                start_time = datetime.fromisoformat(booking['start_time']).strftime('%I:%M %p')
                end_time = datetime.fromisoformat(booking['end_time']).strftime('%I:%M %p')
                
                # Send to mentee
                mentee_message = f"""
Hello {mentee.first_name},

This is a reminder that your mentorship session is scheduled for tomorrow!

Session Details:
- Mentor: {mentor_user.first_name} {mentor_user.last_name}
- Topic: {booking['topic']}
- Date: {session_date}
- Time: {start_time} - {end_time}

{f"Meeting Link: {booking['meeting_link']}" if booking.get('meeting_link') else "Your mentor will share the meeting link."}

We look forward to your session!

Best regards,
Mansa Mentorship Team
                """
                
                send_mail(
                    subject=f"Reminder: Mentorship Session Tomorrow - {session_date}",
                    message=mentee_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentee.email],
                    fail_silently=True,
                )
                
                # Send to mentor
                mentor_message = f"""
Hello {mentor_user.first_name},

This is a reminder that you have a mentorship session scheduled for tomorrow!

Session Details:
- Mentee: {mentee.first_name} {mentee.last_name}
- Topic: {booking['topic']}
- Date: {session_date}
- Time: {start_time} - {end_time}

{f"Meeting Link: {booking['meeting_link']}" if booking.get('meeting_link') else "Please share your meeting link with the mentee."}

Best regards,
Mansa Mentorship Team
                """
                
                send_mail(
                    subject=f"Reminder: Mentorship Session Tomorrow - {session_date}",
                    message=mentor_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentor_user.email],
                    fail_silently=True,
                )
                
                reminder_count += 1
                
            except Exception as e:
                logger.error(f"Error sending reminder for booking {booking['id']}: {e}")
                continue
        
        logger.info(f"Sent {reminder_count} session reminders for {tomorrow_date}")
        return reminder_count
        
    except Exception as e:
        logger.error(f"Error in send_session_reminder_24h task: {e}")
        return 0


@shared_task
def send_booking_status_update_email(booking_id: str, old_status: str, new_status: str):
    """
    Send email when booking status changes (confirmed, cancelled, completed).
    """
    try:
        # Fetch booking details
        booking = supabase_client._client.table('mentorship_bookings').select('*').eq('id', booking_id).single().execute().data
        
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return
        
        # Fetch users
        mentor_data = supabase_client._client.table('mentors').select('*').eq('id', booking['mentor_id']).single().execute().data
        mentee = User.objects.filter(id=booking['mentee_id']).first()
        mentor_user = User.objects.filter(id=mentor_data['user_id']).first()
        
        if not mentee or not mentor_user:
            logger.error(f"User data not found for booking {booking_id}")
            return
        
        # Format session details
        session_date = datetime.fromisoformat(booking['session_date']).strftime('%B %d, %Y')
        start_time = datetime.fromisoformat(booking['start_time']).strftime('%I:%M %p')
        
        # Status-specific messages
        status_messages = {
            'confirmed': {
                'subject': f"Session Confirmed - {session_date}",
                'body': f"Your mentorship session has been confirmed by {mentor_user.first_name}!"
            },
            'cancelled_by_mentor': {
                'subject': f"Session Cancelled - {session_date}",
                'body': f"Unfortunately, {mentor_user.first_name} had to cancel the session. Please reschedule at your convenience."
            },
            'cancelled_by_mentee': {
                'subject': f"Session Cancelled - {session_date}",
                'body': f"{mentee.first_name} has cancelled the session."
            },
            'completed': {
                'subject': f"Session Completed - {session_date}",
                'body': "Thank you for completing your mentorship session! Please consider leaving feedback."
            }
        }
        
        status_info = status_messages.get(new_status)
        if not status_info:
            return
        
        # Send to appropriate recipient
        recipient = mentee.email if 'mentor' not in new_status else mentor_user.email
        recipient_name = mentee.first_name if 'mentor' not in new_status else mentor_user.first_name
        
        message = f"""
Hello {recipient_name},

{status_info['body']}

Session Details:
- Topic: {booking['topic']}
- Date: {session_date}
- Time: {start_time}

Best regards,
Mansa Mentorship Team
        """
        
        send_mail(
            subject=status_info['subject'],
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        
        logger.info(f"Status update email sent for booking {booking_id}: {old_status} -> {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending status update email: {e}")
        return False
