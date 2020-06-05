import json

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames import statuses
from pomodorr.frames.models import DateFrame
from pomodorr.frames.routing import frames_application

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def test_connect_websocket(task_instance, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    connected, _ = await communicator.connect()

    assert connected
    await communicator.disconnect()


@pytest.mark.parametrize(
    'tested_frame_type',
    [DateFrame.pomodoro_type, DateFrame.break_type, DateFrame.pause_type]
)
async def test_start_frame(tested_frame_type, task_instance, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    await communicator.connect()

    assert await database_sync_to_async(task_instance.frames.exists)() is False

    await communicator.send_json_to({
        'type': 'frame_start',
        'frame_type': tested_frame_type
    })

    response = await communicator.receive_json_from()

    assert response['level'] == statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_SUCCESS]
    assert response['code'] == statuses.LEVEL_TYPE_SUCCESS
    assert response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_STARTED]
    assert response['data']['date_frame_id'] is not None
    assert database_sync_to_async(task_instance.frames.exists)()

    await communicator.disconnect()


@pytest.mark.parametrize(
    'tested_frame_type',
    [DateFrame.pomodoro_type, DateFrame.break_type, DateFrame.pause_type]
)
async def test_channel_group_separation(tested_frame_type, active_user, task_instance,
                                        task_instance_in_second_project):
    communicator_1 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator_2 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance_in_second_project.id}/')
    communicator_1.scope['user'] = active_user
    communicator_2.scope['user'] = active_user
    communicator_1_connected, _ = await communicator_1.connect()
    communicator_2_connected, _ = await communicator_2.connect()

    assert communicator_1_connected
    assert communicator_2_connected
    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()

    await communicator_1.send_json_to({
        'type': 'frame_start',
        'frame_type': tested_frame_type
    })

    assert await communicator_1.receive_nothing() is False
    assert await communicator_2.receive_nothing()

    await communicator_1.disconnect()
    await communicator_2.disconnect()


@pytest.mark.parametrize(
    'tested_frame_type',
    [DateFrame.pomodoro_type, DateFrame.break_type, DateFrame.pause_type]
)
async def test_connection_discarded_before_second_connection_established(tested_frame_type, active_user, task_instance):
    communicator_1 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator_2 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator_1.scope['user'] = active_user
    communicator_2.scope['user'] = active_user

    communicator_1_connected, _ = await communicator_1.connect()
    assert communicator_1_connected

    communicator_2_connected, _ = await communicator_2.connect()
    assert communicator_2_connected

    connection_close_response = await communicator_1.receive_output()

    assert connection_close_response['type'] == 'websocket.close'
    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing()

    await communicator_2.send_json_to({
        'type': 'frame_start',
        'frame_type': tested_frame_type
    })

    assert await communicator_1.receive_nothing()
    assert await communicator_2.receive_nothing() is False

    await communicator_2.disconnect()


@pytest.mark.parametrize(
    'tested_frame_type',
    [
        lazy_fixture('pomodoro_in_progress'),
        lazy_fixture('pause_in_progress')
    ]
)
async def test_date_frame_force_finished_and_client_notified(tested_frame_type, active_user, task_instance):
    communicator_1 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator_2 = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator_1.scope['user'] = active_user
    communicator_2.scope['user'] = active_user

    await communicator_1.connect()
    await communicator_2.connect()

    notification_message = await communicator_1.receive_output()

    assert notification_message['type'] == 'websocket.send'
    assert json.loads(notification_message['text'])['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[
        statuses.FRAME_ACTION_FORCE_TERMINATED]

    connection_close_response = await communicator_1.receive_output()
    assert connection_close_response['type'] == 'websocket.close'

    await communicator_1.disconnect()
    await communicator_2.disconnect()


async def test_channel_group_permission(task_instance_for_random_project, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance_for_random_project.id}/')
    communicator.scope['user'] = active_user
    connected, _ = await communicator.connect()

    assert connected is False
