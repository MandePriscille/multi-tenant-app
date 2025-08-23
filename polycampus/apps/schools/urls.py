from django.urls import path
from apps.schools.views import index

urlpatterns = [
    path("index/", index, name="index"),
]