import random
import string
import uuid
from django.conf import settings
from django.db import models
from tenant_users.tenants.models import TenantBase
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin
from django_extensions.db.models import TimeStampedModel, ActivatorModel

from apps.utils.enums import ApprovalStatusType



class BaseModel(TimeStampedModel, ActivatorModel):

    id = models.UUIDField(default=uuid.uuid4, null=False, blank=False, unique=True, primary_key=True)
    is_deleted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, null=True, blank=True)
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='%(class)s_created_by')  # noqa

    class Meta:
        abstract = True
        ordering = ("created",)


class Organisation(BaseModel, TenantBase):
 
    name = models.CharField(help_text=_("name of the client"), max_length=100)

    email = models.EmailField(help_text=_('organisation email'), null=True, blank=True)

    description = models.TextField(help_text=_('organisation description'), null=True, blank=True)

    organisation_code = models.CharField(max_length=128, unique=True, null=True, blank=True)
    
    created_on = models.DateField(auto_now_add=True)
    
    is_active = models.BooleanField(default=True)
            
    quater = models.CharField(max_length=150, blank=True, null=True)
    
    address_line1 = models.CharField(max_length=150, blank=True, null=True)
    
    address_line2 = models.CharField(max_length=150, blank=True, null=True)
    
    approval_status = models.CharField(choices=ApprovalStatusType.choices, default=ApprovalStatusType.PENDING, max_length=100)

    phone = models.CharField(max_length=150, blank=True, null=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_organisations",
        null=True,
        blank=True,
        help_text=_("The user who owns this organisation"),
    )

    auto_drop_schema = False # meaning that the schema will not be dropped when the tenant is deleted
    
    def generate_unique_organisation_code(self):
        """Generate a unique 8-character alphanumeric organisation code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Organisation.objects.filter(organisation_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        """Override save to ensure organisation_code is set."""
        if not self.organisation_code:
            self.organisation_code = self.generate_unique_organisation_code()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Domain(DomainMixin):
    
    def delete_domain(self):
        # check if the domain is primary
        if self.is_primary:
            raise Exception("Cannot delete the primary domain")
        
        # check if the domain is used by any tenant
        if self.tenant:
            raise Exception("Cannot delete a domain that is used by a tenant")
        
        super().delete()


