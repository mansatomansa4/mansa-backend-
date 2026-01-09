"""Root URL configuration and lightweight analytics admin endpoints."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import analytics
from apps.users.permissions import IsAdmin


class AnalyticsOverviewView(APIView):
    """Analytics overview endpoint with JWT authentication."""

    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(analytics.overview_metrics())


class AnalyticsUsersView(APIView):
    """Analytics users endpoint with JWT authentication."""

    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(analytics.user_metrics())


class AnalyticsProjectsView(APIView):
    """Analytics projects endpoint with JWT authentication."""

    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(analytics.project_metrics())


class AnalyticsEmailsView(APIView):
    """Analytics emails endpoint with JWT authentication."""

    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(analytics.email_metrics())


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
    path("api/", include("apps.events.urls")),
    path("api/v1/mentorship/", include("apps.mentorship.urls")),
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
