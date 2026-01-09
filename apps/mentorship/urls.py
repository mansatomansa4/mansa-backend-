"""
Mentorship App URL Configuration with API Versioning
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MentorViewSet, BookingViewSet, ExpertiseViewSet

app_name = 'mentorship'

router = DefaultRouter()
router.register(r'mentors', MentorViewSet, basename='mentor')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'expertise', ExpertiseViewSet, basename='expertise')

urlpatterns = [
    path('', include(router.urls)),
]
