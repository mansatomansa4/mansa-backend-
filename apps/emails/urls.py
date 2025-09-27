from rest_framework.routers import DefaultRouter

from .views import EmailCampaignViewSet, EmailLogViewSet, EmailTemplateViewSet

router = DefaultRouter()
router.register("emails/templates", EmailTemplateViewSet, basename="email-template")
router.register("emails/campaigns", EmailCampaignViewSet, basename="email-campaign")
router.register("emails/logs", EmailLogViewSet, basename="email-log")

urlpatterns = router.urls
