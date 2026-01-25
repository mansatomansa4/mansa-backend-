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
        
        # Get end time for full time range display
        end_time = datetime.fromisoformat(booking['end_time']).strftime('%I:%M %p') if booking.get('end_time') else ''
        time_display = f"{start_time} - {end_time}" if end_time else start_time
        
        # Handle confirmed status - send detailed confirmation to mentee
        if new_status == 'confirmed':
            # Send confirmation email to mentee
            mentee_message = f"""
Hello {mentee.first_name},

Great news! Your mentorship session has been CONFIRMED by {mentor_user.first_name} {mentor_user.last_name}!

🎉 SESSION CONFIRMED

Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"🔗 Meeting Link: {booking.get('meeting_link') or booking.get('meeting_url')}" if booking.get('meeting_link') or booking.get('meeting_url') else "Your mentor will share the meeting link before the session."}

What to do next:
• Add this session to your calendar
• Prepare any questions or topics you'd like to discuss
• Join the meeting on time

You can view and manage your bookings from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
            """
            
            send_mail(
                subject=f"🎉 Session Confirmed with {mentor_user.first_name} - {session_date}",
                message=mentee_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee.email],
                fail_silently=False,
            )
            
            logger.info(f"Confirmation email sent to mentee {mentee.email} for booking {booking_id}")
            return True
        
        # Handle cancellation by mentor - notify mentee
        elif new_status == 'cancelled_by_mentor':
            mentee_message = f"""
Hello {mentee.first_name},

Unfortunately, your mentorship session has been cancelled by {mentor_user.first_name}.

Cancelled Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

We apologize for the inconvenience. You can browse other available mentors and book a new session from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
            """
            
            send_mail(
                subject=f"Session Cancelled - {session_date}",
                message=mentee_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee.email],
                fail_silently=False,
            )
            
            logger.info(f"Cancellation email sent to mentee {mentee.email} for booking {booking_id}")
            return True
        
        # Handle cancellation by mentee - notify mentor
        elif new_status == 'cancelled_by_mentee':
            mentor_message = f"""
Hello {mentor_user.first_name},

A mentorship session has been cancelled by the mentee.

Cancelled Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👤 Mentee: {mentee.first_name} {mentee.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

Your time slot is now available for other bookings.

Best regards,
Mansa Mentorship Team
            """
            
            send_mail(
                subject=f"Session Cancelled by Mentee - {session_date}",
                message=mentor_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentor_user.email],
                fail_silently=False,
            )
            
            logger.info(f"Cancellation email sent to mentor {mentor_user.email} for booking {booking_id}")
            return True
        
        # Handle session completed - notify both
        elif new_status == 'completed':
            # Notify mentee
            mentee_message = f"""
Hello {mentee.first_name},

Thank you for completing your mentorship session!

Completed Session:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We'd love to hear your feedback! Please take a moment to rate your session and leave a review for your mentor.

Best regards,
Mansa Mentorship Team
            """

            send_mail(
                subject=f"Session Completed - Thank You! - {session_date}",
                message=mentee_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee.email],
                fail_silently=False,
            )

            logger.info(f"Completion email sent to mentee {mentee.email} for booking {booking_id}")
            return True

        # Handle rejected status - notify mentee
        elif new_status == 'rejected':
            mentee_message = f"""
Hello {mentee.first_name},

Unfortunately, your mentorship session request has been declined by {mentor_user.first_name}.

Declined Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Reason: {booking.get('rejection_reason')}" if booking.get('rejection_reason') else ""}

Don't be discouraged! You can browse other available mentors and book a new session from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
            """

            send_mail(
                subject=f"Session Request Declined - {session_date}",
                message=mentee_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee.email],
                fail_silently=False,
            )

            logger.info(f"Rejection email sent to mentee {mentee.email} for booking {booking_id}")
            return True

        # Handle cancelled status (generic)
        elif new_status == 'cancelled':
            cancelled_by = booking.get('cancelled_by', 'unknown')

            if cancelled_by == 'mentor':
                # Notify mentee
                mentee_message = f"""
Hello {mentee.first_name},

Your mentorship session has been cancelled by the mentor.

Cancelled Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

We apologize for the inconvenience. You can browse other available mentors from your Mansa dashboard.

Best regards,
Mansa Mentorship Team
                """

                send_mail(
                    subject=f"Session Cancelled - {session_date}",
                    message=mentee_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentee.email],
                    fail_silently=False,
                )
            else:
                # Notify mentor
                mentor_message = f"""
Hello {mentor_user.first_name},

A mentorship session has been cancelled by the mentee.

Cancelled Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👤 Mentee: {mentee.first_name} {mentee.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Reason: {booking.get('cancellation_reason')}" if booking.get('cancellation_reason') else ""}

Your time slot is now available for other bookings.

Best regards,
Mansa Mentorship Team
                """

                send_mail(
                    subject=f"Session Cancelled by Mentee - {session_date}",
                    message=mentor_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentor_user.email],
                    fail_silently=False,
                )

            logger.info(f"Cancellation email sent for booking {booking_id}")
            return True

        # Handle rescheduled status - notify both
        elif new_status == 'rescheduled':
            # Notify mentee
            mentee_message = f"""
Hello {mentee.first_name},

Your mentorship session has been rescheduled.

New Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 New Date: {session_date}
⏰ New Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please update your calendar with the new date and time.

Best regards,
Mansa Mentorship Team
            """

            send_mail(
                subject=f"Session Rescheduled - {session_date}",
                message=mentee_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentee.email],
                fail_silently=False,
            )

            # Notify mentor
            mentor_message = f"""
Hello {mentor_user.first_name},

A mentorship session has been rescheduled.

New Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 New Date: {session_date}
⏰ New Time: {time_display}
👤 Mentee: {mentee.first_name} {mentee.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please update your calendar with the new date and time.

Best regards,
Mansa Mentorship Team
            """

            send_mail(
                subject=f"Session Rescheduled - {session_date}",
                message=mentor_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mentor_user.email],
                fail_silently=False,
            )

            logger.info(f"Reschedule email sent for booking {booking_id}")
            return True

        # Handle no_show status
        elif new_status == 'no_show':
            no_show_by = booking.get('no_show_by', 'unknown')

            if no_show_by == 'mentee':
                # Notify mentee
                mentee_message = f"""
Hello {mentee.first_name},

You have been marked as a no-show for your scheduled mentorship session.

Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {session_date}
⏰ Time: {time_display}
👨‍🏫 Mentor: {mentor_user.first_name} {mentor_user.last_name}
📝 Topic: {booking['topic']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If this was a mistake, please contact the mentor or reach out to support.

Best regards,
Mansa Mentorship Team
                """

                send_mail(
                    subject=f"Missed Session - {session_date}",
                    message=mentee_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[mentee.email],
                    fail_silently=False,
                )

            logger.info(f"No-show email sent for booking {booking_id}")
            return True

        logger.info(f"Status update email sent for booking {booking_id}: {old_status} -> {new_status}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending status update email: {e}")
        return False
