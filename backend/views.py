from django.shortcuts import render
from django.http import FileResponse, Http404
from django.conf import settings
import os

# Create your views here.
def dashboard_view(request):
    return render(request, 'Dashboard/index.html')


def serve_media(request, path):
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path)) 
    if not full_path.startswith(os.path.normpath(settings.MEDIA_ROOT)):
        raise Http404("File not found.")
    if not os.path.isfile(full_path):
        raise Http404("File not found.")
    return FileResponse(open(full_path, 'rb'))