from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response    
from .serializers import *
from backend.models import File
from datetime import datetime 
from backend.tasks import process_file
from backend.util.review_processing import start_processing
from backend.util.review_visualiser import main
import os

class FileView(APIView):
    serializer_class = FileSerializer

    def get(self, request, *args, **kwargs):
        try: 
            serializer = self.serializer_class(File.objects.all().order_by('-id'), many=True) 
            response_data = list(serializer.data)
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error fetching files: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            file = data.get('file', None) 

            if not file:
                return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST) 
            
            if not file.name.endswith(('.xls', '.xlsx')):
                return Response({"error": "Invalid file type. Only Excel files are allowed."}, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = File.objects.create(file=file) 
            job_id = process_file.apply_async(args=[uploaded_file.id]) 
            uploaded_file.job_id = job_id.id
            uploaded_file.save() 

            return Response({"id": uploaded_file.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Error processing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST) 
