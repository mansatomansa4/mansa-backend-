from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AdminUserViewSet, CustomTokenObtainPairView, MeView, RegisterView, email_login

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("email-login/", email_login, name="email_login"),
]

urlpatterns += router.urls
