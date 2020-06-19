import json

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames import statuses
from pomodorr.frames.models import DateFrame
from pomodorr.frames.routing import frames_application
from pomodorr.frames.selectors.date_frame_selector import get_finished_date_frames_for_task

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
async def test_start_and_finish_date_frame(tested_frame_type, task_instance, active_user):
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

    started_date_frame_id = response['data']['date_frame_id']

    assert started_date_frame_id is not None
    assert await database_sync_to_async(task_instance.frames.exists)()

    await communicator.send_json_to({
        'type': 'frame_finish',
        'date_frame_id': started_date_frame_id
    })

    response = await communicator.receive_json_from()

    assert response['level'] == statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_SUCCESS]
    assert response['code'] == statuses.LEVEL_TYPE_SUCCESS
    assert response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED]

    assert await database_sync_to_async(get_finished_date_frames_for_task(task=task_instance).exists)()

    await communicator.disconnect()


async def test_start_and_finish_pomodoro_with_pause_inside(task_instance, active_user):
    communicator = WebsocketCommunicator(frames_application, f'date_frames/{task_instance.id}/')
    communicator.scope['user'] = active_user
    await communicator.connect()

    await communicator.send_json_to({
        'type': 'frame_start',
        'frame_type': DateFrame.pomodoro_type
    })

    pomodoro_started_response = await communicator.receive_json_from()
    assert pomodoro_started_response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_STARTED]

    started_pomodoro_id = pomodoro_started_response['data']['date_frame_id']

    await communicator.send_json_to({
        'type': 'frame_start',
        'frame_type': DateFrame.pause_type
    })

    pause_started_response = await communicator.receive_json_from()
    assert pause_started_response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_STARTED]

    pomodoro = await database_sync_to_async(DateFrame.objects.get)(id=started_pomodoro_id)
    assert pomodoro.end is None  # check if pomodoro hasn't been stopped by starting a pause date frame

    started_pause_id = pause_started_response['data']['date_frame_id']
    pause = await database_sync_to_async(DateFrame.objects.get)(id=started_pause_id)

    assert pause.end is None

    await communicator.send_json_to({
        'type': 'frame_finish',
        'date_frame_id': started_pause_id
    })

    pause_finished_response = await communicator.receive_json_from()
    assert pause_finished_response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED]

    await database_sync_to_async(pause.refresh_from_db)()

    assert pause.end is not None  # pause should be finished here
    await database_sync_to_async(pomodoro.refresh_from_db)()
    assert pomodoro.end is None

    await communicator.send_json_to({
        'type': 'frame_finish',
        'date_frame_id': started_pomodoro_id
    })

    pomodoro_finished_response = await communicator.receive_json_from()
    await database_sync_to_async(pomodoro.refresh_from_db)()

    assert pomodoro.end is not None  # Only now the pomodoro is expected to be finished
    assert pomodoro_finished_response['action'] == statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED]
    assert await database_sync_to_async(get_finished_date_frames_for_task(task=task_instance).count)() == 2

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
