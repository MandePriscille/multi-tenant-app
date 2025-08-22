from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist


class UserManager(BaseUserManager):
   
    # def get_queryset(self) -> QuerySet:
    #     return super().get_queryset().filter(is_deleted=False)

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user


    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(password=password, email=email, **extra_fields)
    

class UserRoleManager(BaseUserManager):
    """
    User role manager filtered by group.
    """
    def __init__(self, group_name, *args, **kwargs):
        self.group_name = group_name
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        try:
            group = Group.objects.get(name=self.group_name)
        except ObjectDoesNotExist:
            # If the group does not exist, return an empty queryset
            return super().get_queryset().none()

        # Safely filter users who have the specified group
        return super().get_queryset().filter(
            usertenantpermissions__group=group
        )


class PolycampusManager(UserRoleManager):
    
    def __init__(self, *args, **kwargs):
        super().__init__(group_name="polycampus", *args, **kwargs)


class AdminTenantManager(UserRoleManager):
    """
    Description: AdminTenant model manager.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(group_name="AdminTenant", *args, **kwargs)


class TeacherUserManager(UserRoleManager):
    """
    Description: TeacherUser model manager.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(group_name="TeacherUser", *args, **kwargs)


class StudentUserManager(UserRoleManager):
    """
    Description: studentUser model manager.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(group_name="studentUser", *args, **kwargs)


