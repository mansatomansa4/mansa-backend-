"""
Mentorship App URL Configuration with API Versioning

Available endpoints:

MENTORS:
- GET    /mentors/                    - List all approved mentors
- GET    /mentors/{id}/               - Get mentor profile (use 'me' for current user)
- GET    /mentors/my_profile/         - Get current user's mentor profile
- GET    /mentors/dashboard/          - Get mentor dashboard data
- GET    /mentors/stats/              - Get mentor statistics
- GET    /mentors/search/             - Search mentors
- POST   /mentors/create_profile/     - Create mentor profile
- PATCH  /mentors/update_my_profile/  - Update current mentor's profile
- PATCH  /mentors/{id}/update_profile/- Update mentor profile by ID
- POST   /mentors/{id}/upload_photo/  - Upload profile photo
- DELETE /mentors/{id}/delete_photo/  - Delete profile photo
- GET    /mentors/{id}/availability/  - Get mentor's availability
- GET    /mentors/{id}/reviews/       - Get mentor's reviews

BOOKINGS:
- GET    /bookings/                   - List bookings (role=mentee|mentor, status=...)
- GET    /bookings/{id}/              - Get booking details
- POST   /bookings/                   - Create new booking
- PATCH  /bookings/{id}/confirm/      - Confirm booking (mentor)
- PATCH  /bookings/{id}/reject/       - Reject booking (mentor)
- PATCH  /bookings/{id}/cancel/       - Cancel booking
- PATCH  /bookings/{id}/complete/     - Mark as completed (mentor)
- PATCH  /bookings/{id}/no_show/      - Mark as no-show (mentor)
- PATCH  /bookings/{id}/reschedule/   - Reschedule booking
- PATCH  /bookings/{id}/add_meeting_link/ - Add Zoom/Meet link
- PATCH  /bookings/{id}/add_notes/    - Add session notes
- POST   /bookings/{id}/add_feedback/ - Add review/feedback

AVAILABILITY:
- GET    /availability/               - List current mentor's availability
- GET    /availability/me/            - Alias for above
- POST   /availability/               - Create availability slot
- POST   /availability/bulk/          - Create multiple slots
- PATCH  /availability/{id}/          - Update slot
- DELETE /availability/{id}/          - Delete slot
- DELETE /availability/clear/         - Clear all availability

MENTEE:
- GET    /mentee/dashboard/           - Get mentee dashboard
- GET    /mentee/history/             - Get session history
- GET    /mentee/recommended/         - Get recommended mentors
- GET    /mentee/bookings/            - Get mentee's bookings

EXPERTISE:
- GET    /expertise/                  - List expertise categories
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MentorViewSet,
    BookingViewSet,
    ExpertiseViewSet,
    AvailabilityViewSet,
    MenteeDashboardViewSet
)

app_name = 'mentorship'

router = DefaultRouter()
router.register(r'mentors', MentorViewSet, basename='mentor')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'expertise', ExpertiseViewSet, basename='expertise')
router.register(r'availability', AvailabilityViewSet, basename='availability')
router.register(r'mentee', MenteeDashboardViewSet, basename='mentee')

urlpatterns = [
    path('', include(router.urls)),
]
