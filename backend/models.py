from django.db import models 
from .constants import FileStatus, choices

class File(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=choices(FileStatus), default=FileStatus.PENDING)
    results = models.JSONField(null=True, blank=True)
    job_id = models.CharField(max_length=300, null=True, blank=True, db_index=True)

    results_excel = models.FileField(upload_to='results/', null=True, blank=True)
    negative_heatmap_on_location = models.JSONField(null=True, blank=True)
    mention_frequency_heatmap = models.JSONField(null=True, blank=True)
    weighted_severity_heatmap = models.JSONField(null=True, blank=True)
    priority_matrix = models.JSONField(null=True, blank=True)
    breakdown_jsons = models.JSONField(null=True, blank=True)
    insights_report = models.TextField(null=True, blank=True)