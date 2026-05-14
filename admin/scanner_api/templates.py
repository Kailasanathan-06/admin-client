from pathlib import Path
from django.http import FileResponse
from django.shortcuts import render
from django.conf import settings


def dashboard(request):
    return render(request, "dashboard.html")


def client_detail(request, key):
    return render(request, "client_detail.html", {"client_key": key})


def settings_page(request):
    return render(request, "settings.html")


def static_files(request, filename):
    static_dir = Path(settings.BASE_DIR) / "static"
    file_path = static_dir / filename
    if not file_path.exists():
        from django.http import Http404
        raise Http404("Static file not found")
    return FileResponse(open(file_path, "rb"))
