from django.db.models.signals import post_save
from django.dispatch import receiver
from back.models import User
from .models import InvoiceSettings, NumberingTemplate


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        # Создаем настройки счетов
        InvoiceSettings.objects.create(user=instance)

        # Создаем шаблон по умолчанию
        NumberingTemplate.objects.create(
            user=instance,
            name="Default",
            prefix='INV-',
            is_default=True
        )
