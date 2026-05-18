from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def client_detail(request, key):
    return render(request, "client_detail.html", {"client_key": key})


@login_required
def settings_page(request):
    return render(request, "settings.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            from .models import ActivityLog
            ActivityLog.objects.create(action="login", details=f"Admin user {username} logged in")
            next_url = request.POST.get("next", "/")
            return redirect(next_url)
        return render(request, "login.html", {"error": "Invalid username or password"})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/login/")
