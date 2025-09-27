from rest_framework import serializers

from .models import EmailCampaign, EmailLog, EmailTemplate


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at"]


class EmailCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailCampaign
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "status", "sent_at"]


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = "__all__"
        read_only_fields = [
            "recipient",
            "campaign",
            "template",
            "subject",
            "status",
            "error_message",
            "sent_at",
            "opened_at",
            "clicked_at",
            "created_at",
        ]
