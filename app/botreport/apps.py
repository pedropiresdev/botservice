from django.apps import AppConfig



class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.botreport'

    def ready(self):
        from app.botreport.pubsub_service import publisher, listener

        try:
            publisher()
            listener()
        
        except Exception as error:
            print(error)