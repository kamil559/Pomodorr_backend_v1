from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def task_completed_notify_channel(sender, task, **kwargs):
    channel_layer = get_channel_layer()
    group_name = f'task_{task.id}'

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'frame.notify_frame_terminated'
        }
    )
