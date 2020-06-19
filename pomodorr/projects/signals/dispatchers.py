from django.dispatch import Signal

notify_force_finish = Signal(providing_args=['task'])
