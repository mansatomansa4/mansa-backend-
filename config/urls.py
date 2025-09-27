"""Root URL configuration and lightweight analytics admin endpoints."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views import View
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.core import analytics
from apps.users.permissions import IsAdmin


class AdminAnalyticsBase(View):  # pragma: no cover - thin wrappers
    permission_classes = [IsAdmin]

    def dispatch(self, request, *args, **kwargs):  # type: ignore
        # Manual permission check since we are not using DRF here for lightweight endpoints
        user = request.user
        if not (user.is_authenticated and getattr(user, "role", "") in ["admin", "super_admin"]):
            return JsonResponse({"detail": "Forbidden"}, status=403)
        return super().dispatch(request, *args, **kwargs)


class AnalyticsOverviewView(AdminAnalyticsBase):
    def get(self, request):  # type: ignore
        return JsonResponse(analytics.overview_metrics())


class AnalyticsUsersView(AdminAnalyticsBase):
    def get(self, request):  # type: ignore
        return JsonResponse(analytics.user_metrics())


class AnalyticsProjectsView(AdminAnalyticsBase):
    def get(self, request):  # type: ignore
        return JsonResponse(analytics.project_metrics())


class AnalyticsEmailsView(AdminAnalyticsBase):
    def get(self, request):  # type: ignore
        return JsonResponse(analytics.email_metrics())


def root_view(request):  # pragma: no cover - simple convenience endpoint
    base = request.build_absolute_uri("/").rstrip("/")
    api_base = f"{base}/api"
    return JsonResponse(
        {
            "service": "mansa-backend",
            "endpoints": {
                "health": f"{api_base}/health/",
                "users": f"{api_base}/users/",
                "platform": f"{api_base}/platform/",
                "schema": f"{api_base}/schema/",
                "docs": f"{api_base}/docs/",
                "redoc": f"{api_base}/redoc/",
            },
        }
    )


urlpatterns = [
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/platform/", include("apps.platform.urls")),
    path("api/", include("apps.emails.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path(
        "api/admin/analytics/overview/", AnalyticsOverviewView.as_view(), name="analytics-overview"
    ),
    path("api/admin/analytics/users/", AnalyticsUsersView.as_view(), name="analytics-users"),
    path(
        "api/admin/analytics/projects/", AnalyticsProjectsView.as_view(), name="analytics-projects"
    ),
    path("api/admin/analytics/emails/", AnalyticsEmailsView.as_view(), name="analytics-emails"),
]
