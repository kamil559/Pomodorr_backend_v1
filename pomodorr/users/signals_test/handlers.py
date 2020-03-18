import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from pomodorr.users.services import UserDomainModel

# User = get_user_model()


# def post_user_create_signal(sender, instance, created, **kwargs):
#     if created and not instance.is_active:
#         UserDomainModel.send_account_activation_mail(user_object=instance)
#
#
# if not settings.DEBUG:
#     post_save.connect(receiver=post_user_create_signal, sender=User,
#                       dispatch_uid="pomodoro_app.users.user.send_account_activation_mail")
