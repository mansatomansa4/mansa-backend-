from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, EventRegistrationViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'registrations', EventRegistrationViewSet, basename='event-registration')

urlpatterns = [
    path('', include(router.urls)),
    # Custom registration endpoint for simpler frontend integration
    path('events/register/', EventRegistrationViewSet.as_view({'post': 'create'}), name='event-register'),
]
