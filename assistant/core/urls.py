from django.contrib import admin
from django.urls import path
from .views import Core

urlpatterns = [
    path('', Core.as_view(), name="core"),
]
