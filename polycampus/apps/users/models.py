import logging

from django.contrib.postgres.fields import ArrayField
from django.core.mail import send_mail
from django.db import connection, models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tenant_users.tenants.models import UserProfile
from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from apps.core.models import BaseModel
from apps.utils.enums import ApprovalStatusType, GenderType, GROUPS, ProfileType
from .manager import *

logger = logging.getLogger(__name__)

class User(UserProfile):
   
    organisation_code = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    email = models.EmailField(_("email address"),  max_length=254, blank=False, null=False, unique=True)
    username = models.CharField(_("username"), max_length=150, blank=False, null=False, unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)
    is_staff = models.BooleanField(_("staff status"), default=False,
                                   help_text=_("Designates whether the user can log into this admin site."))
    is_active = models.BooleanField(_("active"), default=False,
                                    help_text=_(
                                        "Designates whether this user should be treated as active. "
                                        "Unselect this instead of deleting accounts."
                                    ))
    is_superuser = models.BooleanField(_("superuser status"), default=False,
                                       help_text=_(
                                           "Designates that this user has all permissions without "
                                           "explicitly assigning them."
                                       ))
    approval_status = models.CharField(
        max_length=25,
        choices=ApprovalStatusType.choices,
        default=ApprovalStatusType.PENDING,
        help_text="Designates whether this user's profile has been approved.",
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    
    is_manualy_deactivated = models.BooleanField(_("Deleted Manually"), default=False)
    

    EMAIL_FIELD = "email"

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('User')
    
    def get_full_name(self) -> str:
        """Return the full name for standard user model compatibility."""
        if self.first_name or self.last_name:
            names = [self.first_name, self.last_name]
            return " ".join(name.capitalize() for name in names if name)
        return self.username

    @property
    def full_name(self) -> str:
        return self.get_full_name()

    def __str__(self) -> str:
        """Return the username."""

        return self.email   

    def email_user(self, subject, message, from_email=None, **kwargs) -> None:
        """Email this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def _has_group(self, group_name: str, schema_name: str) -> bool:
        """Check if the user belongs to a specific group within a schema."""
        try:
            with schema_context(schema_name):
                permissions = getattr(self, "usertenantpermissions", None)
                return permissions.groups.filter(name=group_name).exists() if permissions else False
        except Exception as e:
            logger.error(f"Error checking group {group_name} in schema {schema_name}: {e}")
            return False

    @property
    def is_teacher_user(self) -> bool:
        return self._has_group(GROUPS['teacheruser'], connection.schema_name)

    @property
    def is_student_user(self) -> bool:
        return self._has_group(GROUPS['studentuser'], connection.schema_name)

    @property
    def is_tenant_admin_user(self) -> bool:
        return self._has_group(GROUPS['admintenant'], connection.schema_name)
    
    @property
    def is_polycampus_user(self) -> bool:
        return self._has_group(GROUPS['polycampus'], connection.schema_name)

    @property
    def get_user_role(self) -> str:
        """Return the user's role based on group membership."""
        try:
            if self.is_tenant_admin_user:
                return _("Tenant Admin")
            if self.is_teacher_user:
                return _("Teacher")
            if self.is_student_user:
                return _("Student")
            if self.is_polycampus_user:
                return _("Polycampus")
            return _("Unknown")
        except Exception as e:
            logger.error(f"Error determining user role: {e}")
            return _("Unknown")


class PolycampusUser(User):
    """
    Description: This proxy class help to manage Polycampus users.
    """
    objects = PolycampusManager()

    class Meta:
        proxy = True

    def specific_method_for_jinoo(self):
        # Add behavior specific to polycampus users
        pass


class AdminTenant(User):
    objects = AdminTenantManager()

    class Meta:
        proxy = True

    def specific_method_for_admin_tenant(self):
        # Add behavior specific to Admin Tenant users
        pass


class TeacherUser(User):
    objects = TeacherUserManager()

    class Meta:
        proxy = True

    def specific_method_for_ordinary_user(self):
        # Add behavior specific to Ordinary users
        pass


class StudentUser(User):
    objects = StudentUserManager()

    class Meta:
        proxy = True

    def specific_method_for_premium_user(self):
        # Add behavior specific to Premium users
        pass

class Profile(BaseModel):
    """
    Description: This class help to create a user profile.
    """
    user = models.OneToOneField(User, verbose_name=_("User"), on_delete=models.CASCADE)
    bio = models.CharField(_("Biography"), max_length=1000, null=True, blank=True)
    phone = models.CharField(_("Phone Number"), max_length=50, null=True, blank=True)
    address1 = models.CharField(_("Address 1"), max_length=50, null=True, blank=True)
    address2 = models.CharField(_("Address 2"), max_length=50, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    quater = models.CharField(_("Quater"), max_length=50, null=True, blank=True)
            
    profiletype = models.CharField(
        max_length=50, 
        choices=ProfileType.choices, 
        default=ProfileType.student,
        help_text=_('Which type of profile is this profile'),
        verbose_name=_("Profile Type")
    )
    
    gender = models.CharField(
        max_length=20,
        blank=True,
        choices=GenderType.choices,
        help_text=_("The applicant's gender as per their ID document."),
        verbose_name=_("Gender")
    )
        
    photo = models.ImageField(_("Profile Picture"), upload_to=PathRename('profile-picture'), null=True, blank=True)
    
    documents = models.FileField(_("receipt, student card"), upload_to='verified_documents/', null=True, blank=True)
    
    certifications = models.TextField(_("Certifications, bullet points"), null=True, blank=True)
    
    def __str__(self)->str:
        return f"{self.user.email}- {self.user.first_name }-{self.user.last_name}"
    
    @property
    def get_photo_url(self):
        if self.photo:
            return self.photo.url
        return None
    
    
    def get_user_profile_info(self):
        return {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            'bio': self.bio,
            'phone': self.phone,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'quater': self.quater,
            'gender': self.gender,
            'photo': self.get_photo_url,
            'documents': self.documents.url if self.documents else None,
            'certifications': self.certifications,
            'profiletype': self.profiletype,
        }


class Otp(BaseModel):

    user = models.OneToOneField(User, verbose_name=_("User"), on_delete=models.CASCADE)
    otp_code = models.CharField(_("OTP Code"), max_length=6, null=True, blank=True)
    
