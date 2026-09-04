from django.shortcuts import render
from .models import BusinessHours


def hours_view(request):
    hours = BusinessHours.objects.all()
    return render(request, 'core/hours.html', {'hours': hours})


def home_view(request):
    hours = BusinessHours.objects.all()
    return render(request, 'core/home.html', {'hours': hours})
