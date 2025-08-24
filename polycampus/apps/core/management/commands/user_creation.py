import random
import string

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context
from tenant_users.permissions.models import UserTenantPermissions

from apps.core.models import Organisation
from apps.users.models import User
from apps.utils.enums import ApprovalStatusType, UserGroupName


class Command(BaseCommand):
    help = 'Create a new user for a specific tenant with a specified role'

    def generate_random_password(self, length=12):
        """Generate a random password of specified length."""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write('Starting user creation process...')

        # Collect input from user
        try:
            email = input('Enter user email: ').strip().lower()
            first_name = input('Enter user first name: ').strip()
            last_name = input('Enter user last name: ').strip()
            schema_name = input('Enter tenant schema name (e.g., tenant1 or public): ').strip().lower()
            role = input(f'Enter user role ({", ".join(UserGroupName.values)}): ').strip()
            generate_password = input('Generate random password? (y/n): ').strip().lower()

            if generate_password == 'y':
                password = self.generate_random_password()
                self.stdout.write(f'Generated password: {password}')
            else:
                password = input('Enter user password: ').strip()

            # Validate inputs
            if not email or not first_name or not last_name or not schema_name or not role or not password:
                self.stderr.write('All fields are required.')
                return

            if not Organisation.objects.filter(schema_name=schema_name).exists():
                self.stderr.write(f'Tenant with schema name "{schema_name}" does not exist.')
                return

            if role not in UserGroupName.values:
                self.stderr.write(f'Invalid role. Choose from: {", ".join(UserGroupName.values)}')
                return

            if User.objects.filter(email=email).exists():
                self.stderr.write(f'Email "{email}" is already in use.')
                return

        except KeyboardInterrupt:
            self.stderr.write('\nOperation cancelled by user.')
            return

        # Create user and assign to tenant in a transaction
        try:
            with transaction.atomic():
                # Determine if user should be a superuser/staff
                is_admin_role = role in [UserGroupName.POLYCAMPUS, UserGroupName.TENANT_ADMIN]

                # Create PlatformUser
                user = User(
                    username=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    approval_status=ApprovalStatusType.APPROVED,
                    is_active=True,
                    is_superuser=is_admin_role,
                    is_staff=is_admin_role,
                )
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {email} (Superuser: {is_admin_role})')

                # Assign user to tenant
                tenant = Organisation.objects.get(schema_name=schema_name)
                user.tenants.add(tenant)
                self.stdout.write(f'Assigned user to tenant: {schema_name}')

                # Assign user to role in tenant schema
                with schema_context(schema_name):
                    group, _ = Group.objects.get_or_create(name=role)
                    user_perm, _ = UserTenantPermissions.objects.get_or_create(
                        profile=user,
                        is_staff=is_admin_role,
                        is_superuser=is_admin_role,
                    )
                    user_perm.groups.add(group)
                    user_perm.save()
                    self.stdout.write(f'Assigned user to role: {role}')

                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created user "{email}" for tenant "{schema_name}" with role "{role}"'
                ))

        except Exception as e:
            self.stderr.write(f'Error occurred: {str(e)}')
            self.stderr.write('Rolling back changes...')
            raise  # Let transaction.atomic handle the rollback
