from typing import Any
from django.db import models
from django.utils.translation import gettext_lazy as _

class GenderType(models.TextChoices):
    """Enumeration class for gender."""

    MALE: Any = "MALE", _("Male")
    FEMALE: Any = "FEMALE", _("Female")
    

class ApprovalStatusType(models.TextChoices):
    """Enumeration class for user approval status."""

    PENDING: Any = "PENDING", _("Pending")
    APPROVED: Any = "APPROVED", _("Approved")
    DISAPPROVED: Any = "DISAPPROVED", _("Disapproved")
    REMOVED: Any = "REMOVED", _("Removed")


GROUPS = {
    'polycampus': 'polycampus',
    'admintenant': 'AdminTenant',
    'studentuser': 'StudentUser',
    'teacheruser': 'TeacherUser',
}       

class ProfileType(models.TextChoices):
    """Enumerate class for Profile Type"""
    STUDENT: Any = " student", _('student')
    TEACHER: Any = " teacher", _('teacher')
