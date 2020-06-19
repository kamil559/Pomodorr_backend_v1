import factory
import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from pomodorr.frames import statuses
from pomodorr.frames.routing import frames_application
from pomodorr.projects.models import Project
from pomodorr.projects.services.task_service import complete_task


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_task_complete_with_ongoing_date_frame_notifies_channel(task_instance, date_frame_in_progress,
                                                                      active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    await communicator.connect()

    await database_sync_to_async(complete_task)(task=task_instance)

    communicator_notification = await communicator.receive_json_from()

    assert communicator_notification['code'] == statuses.LEVEL_TYPE_WARNING
    assert communicator_notification['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[
        statuses.FRAME_ACTION_FORCE_TERMINATED]

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_task_complete_without_ongoing_date_frame_does_not_notify_channel(task_instance, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    await communicator.connect()

    await database_sync_to_async(complete_task)(task=task_instance)

    assert await communicator.receive_nothing()

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
def test_default_project_is_created_after_user_created(user_model, user_data):
    new_user = user_model.objects.create_user(**user_data)

    assert new_user.projects.exists()


@pytest.mark.django_db(transaction=True)
def test_default_project_is_not_created_after_user_updated(user_model, active_user):
    assert Project.objects.count() == 1

    active_user.email = factory.Faker('email').generate()
    active_user.save()

    assert Project.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_default_project_is_not_created_after_admin_created(user_model, admin_data):
    new_admin = user_model.objects.create_superuser(**admin_data)

    assert Project.objects.filter(user=new_admin).exists() is False
