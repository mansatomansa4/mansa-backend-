from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, EventRegistrationViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'registrations', EventRegistrationViewSet, basename='event-registration')

urlpatterns = [
    # Custom registration endpoint MUST come before router.urls to avoid conflict
    path('events/register/', EventRegistrationViewSet.as_view({'post': 'create'}), name='event-register'),
    path('', include(router.urls)),
]
