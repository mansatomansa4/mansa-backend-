from rest_framework.routers import DefaultRouter

from .views import CommunityMemberViewSet, MemberViewSet, ProjectApplicationViewSet, ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("applications", ProjectApplicationViewSet, basename="project-application")
router.register("members", MemberViewSet, basename="member")
router.register("community-members", CommunityMemberViewSet, basename="community-member")

urlpatterns = router.urls
