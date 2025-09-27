from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Health status indicator")


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):  # type: ignore
        data = {"status": "ok"}
        serializer = HealthSerializer(data)
        return Response(serializer.data)
