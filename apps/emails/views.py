from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsAdmin

from .models import EmailCampaign, EmailLog, EmailTemplate
from .serializers import EmailCampaignSerializer, EmailLogSerializer, EmailTemplateSerializer
from .tasks import send_campaign_emails


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all().order_by("-created_at")
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):  # type: ignore
        serializer.save(created_by=self.request.user)


class EmailCampaignViewSet(viewsets.ModelViewSet):
    queryset = EmailCampaign.objects.select_related("template").all().order_by("-created_at")
    serializer_class = EmailCampaignSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):  # type: ignore
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status not in ["draft", "scheduled"]:
            return Response(
                {"detail": f"Cannot send campaign in status {campaign.status}"}, status=400
            )
        campaign.status = "sending"
        campaign.save(update_fields=["status"])
        send_campaign_emails.delay(campaign.id)
        return Response({"detail": "Campaign queued"})


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        EmailLog.objects.select_related("campaign", "recipient", "template")
        .all()
        .order_by("-created_at")
    )
    serializer_class = EmailLogSerializer
    permission_classes = [IsAdmin]
