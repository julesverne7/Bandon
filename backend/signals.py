import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


from backend.models import File
from backend.constants import FileStatus

@receiver(post_save, sender=File)
def file_post_save(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    group_name = "all_users"
    filename = instance.file.name.split('/')[-1]
    upload_date = instance.uploaded_at.isoformat()
    message = {
        'id': instance.id,
        'status': instance.status,
        'job_id': instance.job_id,
        'file_name': filename,
        'uploaded_at': upload_date,
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_message',
            'message': json.dumps(message)
        }
    )
    
post_save.connect(file_post_save, sender=File)