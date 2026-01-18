from rest_framework.routers import DefaultRouter

from .views import (
    EducationCohortApplicationViewSet,
    MemberViewSet,
    ProjectApplicationViewSet,
    ProjectViewSet,
    ResearchCohortApplicationViewSet,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("applications", ProjectApplicationViewSet, basename="project-application")
router.register("members", MemberViewSet, basename="member")

# Cohort application endpoints
router.register("research-cohort", ResearchCohortApplicationViewSet, basename="research-cohort")
router.register("education-cohort", EducationCohortApplicationViewSet, basename="education-cohort")

urlpatterns = router.urls
