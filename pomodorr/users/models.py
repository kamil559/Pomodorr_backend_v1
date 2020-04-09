import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.files import storage
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import When, BooleanField, Case
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pomodorr.tools.utils import get_default_domain


class UserManager(BaseUserManager):

    def get_queryset(self):
        return super(UserManager, self).get_queryset().annotate(is_blocked=Case(
            When(blocked_until__isnull=False, then=True),
            default=False, output_field=BooleanField())
        )

    def active_standard_users(self):
        return self.get_queryset().filter(
            is_active=True,
            blocked_until__isnull=True,
            is_superuser=False,
            is_staff=False
        )

    def non_active_standard_users(self):
        return self.get_queryset().filter(
            is_active=False,
            blocked_until__isnull=True,
            is_superuser=False,
            is_staff=False
        )

    def blocked_standard_users(self):
        return self.get_queryset().filter(
            blocked_until__isnull=False,
            is_superuser=False,
            is_staff=False
        )

    def ready_to_unblock_users(self):
        return self.get_queryset().filter(
            blocked_until__isnull=False,
            blocked_until__lt=timezone.now()
        )

    def _create_user(self, username, email, password, is_active, **extra_fields):
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, is_active=is_active, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username=None, password=None, is_active=False, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, is_active, **extra_fields)

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(username, email, password, is_active=True, **extra_fields)


def user_upload_path(instance, filename):
    return "users/{0}/{1}".format(instance.id, storage.get_valid_filename(filename))


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, null=False, blank=False)
    blocked_until = models.DateTimeField(_("blocked until"), null=True, blank=True)

    avatar = models.FileField(_("avatar"), upload_to=user_upload_path, null=True,
                              validators=(FileExtensionValidator(allowed_extensions=["jpg, jpeg, png"]),))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        ordering = ('date_joined',)

    def get_avatar_url(self):
        if self.avatar:
            return f"{get_default_domain()}{self.avatar.url}"
        return str()
