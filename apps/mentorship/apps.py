from django.apps import AppConfig


class MentorshipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mentorship'
    verbose_name = 'Mentorship Program'

    def ready(self):
        # Import signals if needed in future
        pass
