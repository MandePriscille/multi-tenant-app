from django.urls import path
from apps.users.views import index

urlpatterns = [
    path("index/", index, name="index"),
]