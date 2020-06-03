from pomodorr.user_settings.models import UserSetting


def create_settings(sender, instance, created, **kwargs):
    if created and instance and not instance.is_staff and not instance.is_superuser:
        UserSetting.objects.create(user=instance)
