import io

import factory
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files import File


class UserFactory(factory.DjangoModelFactory):
    email = factory.Faker("email")
    username = factory.Faker("user_name")
    password = factory.Faker('password', length=24, special_chars=True, digits=True, upper_case=True, lower_case=True)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AdminFactory(UserFactory):

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_superuser(*args, **kwargs)


def prepare_registration_data(password2=None, **kwargs):
    if password2 is None:
        password2 = factory.LazyAttribute(lambda user: user.password)
    return factory.build(dict, FACTORY_CLASS=UserFactory, password2=password2, **kwargs)


def prepare_update_data(password_excluded=True, **kwargs):
    update_data = factory.build(dict, FACTORY_CLASS=UserFactory, **kwargs)
    if password_excluded:
        update_data.pop("password")
    return update_data


def prepare_file_bytes_to_upload(name='test.jpeg', ext='jpeg', image_mode='RGB', size=(50, 50), color=(256, 0, 0)):
    file_obj = io.BytesIO()
    image = Image.new(image_mode, size=size, color=color)
    image.save(file_obj, format=ext)
    file_obj.seek(0)
    return File(file_obj, name=name)


def prepare_user(number_of_users: int, **kwargs):
    return factory.create_batch(UserFactory, number_of_users, **kwargs)
