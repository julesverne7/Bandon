import json
import os
from celery import shared_task 
from backend.models import File
from backend.settings import MEDIA_ROOT
from backend.constants import FileStatus
from celery.result import AsyncResult
from django.db.models import Q
from django.db import models
from backend.util.review_visualiser import main as visualize_reviews 
from backend.util.review_processing import start_processing 
import numpy as np


def convert_numpy_to_native(obj):
    """Recursively convert numpy arrays and types to native Python types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_to_native(item) for item in obj]
    return obj


def send_message_to_group(group_name="all_users", message={}):
    """Utility function to send a message to a specific channel group."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_message',
            'message': json.dumps(message)
        }
    )

@shared_task(soft_time_limit=15, time_limit=30)
def check_file_status():
    """A periodic task that checks the status of file uploads and updates their status in the database."""
    pending_files = File.objects.filter(~Q(status=FileStatus.COMPLETED) & ~Q(status=FileStatus.FAILED))
    for file in pending_files:
        # Here you would implement the logic to check the actual status of the file processing.
        # For demonstration purposes, we'll just mark them as COMPLETED.
        work_status = AsyncResult(file.job_id).status
        status_mapping = {
            'PENDING': FileStatus.PENDING,
            'STARTED': FileStatus.PROCESSING,
            'SUCCESS': FileStatus.COMPLETED,
            'FAILURE': FileStatus.FAILED,
            'RETRY': FileStatus.PROCESSING,
            'REVOKED': FileStatus.FAILED,
        }
        file.status = status_mapping.get(work_status, FileStatus.PENDING)
        print(f"File ID: {file.id}, Status: {work_status}")
        send_message_to_group(message={
            'id': file.id,
            'status': file.status,
            'job_id': file.job_id,
        })
        file.save() 
    
@shared_task
def process_file(file_id):
    from django.core.files.base import File as DjangoFile
    filepath = os.path.join(str(MEDIA_ROOT), "results", f"file_results_{file_id}.xlsx")

    file = File.objects.get(id=file_id)

    result_df = start_processing(file.file.path, filepath)
    # Replace NaN values with None (JSON null) before converting to dict
    result_df = result_df.replace({np.nan: None})

    # JSONField → dict / list - convert numpy types to native Python types
    file.results = convert_numpy_to_native(result_df.to_dict(orient="records"))
    file.results_excel.save(os.path.basename(filepath), DjangoFile(open(filepath, 'rb')), save=False)
    _key = None
    json_dict = visualize_reviews(filepath, file_id)
    try:
        for key, value in json_dict.items(): 
            print(f"Updating {key} for File ID: {file_id}, which is a type of {type(value)}")
            _key = key
            field = file._meta.get_field(key)
            if isinstance(field, models.JSONField): 
                # Convert all numpy types to native Python types
                setattr(file, key, convert_numpy_to_native(value))
            else:
                setattr(file, key, str(value)) 
        file.save()
    except Exception as e:
        print(f"Error updating visualizations for File ID: {file_id} for {_key}: {e}") 
