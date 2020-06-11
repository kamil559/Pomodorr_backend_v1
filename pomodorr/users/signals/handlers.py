def create_settings(sender, instance, created, **kwargs):
    from pomodorr.user_settings.models import UserSetting

    if created and instance and not instance.is_staff and not instance.is_superuser:
        UserSetting.objects.create(user=instance)


def create_default_project(sender, instance, created, **kwargs):
    from pomodorr.projects.models import Project, Priority

    if created and instance and not instance.is_staff and not instance.is_superuser:
        default_priority = Priority.objects.create(name='Normal', user=instance)
        Project.objects.create(name='Inbox', priority=default_priority, user=instance)
