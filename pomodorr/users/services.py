from django.contrib.auth import get_user_model
from django.db import transaction


User = get_user_model()


class UserDomainModel:

    @staticmethod
    def get_all_users():
        return User.objects.all()

    @staticmethod
    def get_active_standard_users():
        return User.objects.active_standard_users()

    @staticmethod
    def get_non_active_standard_users():
        return User.objects.non_active_standard_users()

    @staticmethod
    def get_blocked_standard_users():
        return User.objects.blocked_standard_users()

    @staticmethod
    def get_ready_to_unblock_users():
        return User.objects.ready_to_unblock_users()

    @staticmethod
    def unblock_users() -> None:
        User.objects.ready_to_unblock_users().update(blocked_until=None)

    @staticmethod
    def create_user(user_data):
        with transaction.atomic():
            return User.objects.create_user(**user_data)
