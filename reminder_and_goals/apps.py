from django.apps import AppConfig

class ReminderAndGoalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reminder_and_goals'
    
    def ready(self):
        # This import MUST be here for signals to work
        import reminder_and_goals.signals