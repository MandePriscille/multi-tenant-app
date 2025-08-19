import uuid
from django.db import models

from django_extensions.db.models import TimeStampedModel, ActivatorModel


class BaseModel(TimeStampedModel, ActivatorModel):
    """
    Name: BaseModel

    Description: This class help to generate an uuid pk for all models means that all
                 the project's models should inherit from this model.

    Author: djoukevin1469@gmail.com
    """
    id = models.UUIDField(default=uuid.uuid4, null=False, blank=False, unique=True, primary_key=True)
    is_deleted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, null=True, blank=True)
    author = models.ForeignKey('main_app.PlatformUser', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='%(class)s_created_by')  # noqa

    class Meta:
        abstract = True
        ordering = ("created",)
