from rest_framework.routers import DefaultRouter

from .views import ProjectApplicationAdminViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register(
    "applications", ProjectApplicationAdminViewSet, basename="project-application-admin"
)

urlpatterns = router.urls
