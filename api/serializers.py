from backend.models import *
from rest_framework import serializers


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "file", "uploaded_at", "status", "results", "job_id", "results_excel",]