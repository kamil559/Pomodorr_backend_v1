import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from pomodorr.frames import statuses
from pomodorr.frames.routing import frames_application
from pomodorr.projects.services.task_service import complete_task

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


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


async def test_task_complete_without_ongoing_date_frame_does_not_notify_channel(task_instance, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    await communicator.connect()

    await database_sync_to_async(complete_task)(task=task_instance)

    assert await communicator.receive_nothing()

    await communicator.disconnect()
