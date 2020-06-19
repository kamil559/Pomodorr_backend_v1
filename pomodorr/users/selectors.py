from django.contrib.auth import get_user_model

User = get_user_model()


def get_all_users():
    return User.objects.all()


def get_active_standard_users():
    return User.objects.active_standard_users()


def get_non_active_standard_users():
    return User.objects.non_active_standard_users()


def get_blocked_standard_users():
    return User.objects.blocked_standard_users()


def get_ready_to_unblock_users():
    return User.objects.ready_to_unblock_users()
