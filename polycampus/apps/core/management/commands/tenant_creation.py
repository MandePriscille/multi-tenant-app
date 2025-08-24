import logging
import random
import string

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context, schema_exists
from tenant_users.permissions.models import UserTenantPermissions

from apps.core.models import Organisation, Domain
from apps.users.models import User
from apps.utils.enums import ApprovalStatusType, UserGroupName

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a new tenant with an admin user and domain interactively'

    def generate_random_password(self, length=12):
        """Generate a random password of specified length."""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write('Starting tenant creation process (SHARED database type only)...')

        # Collect input from user
        try:
            tenant_name = input('Enter tenant name: ').strip()
            self.stdout.write('Recommendation: For the public (principal) tenant, use schema name "public".')
            schema_name = input('Enter schema name (unique, e.g., tenant1): ').strip().lower()
            quater = input('Enter quater  (e.g., marche b): ').strip().upper()
            address_line1 = input('Enter address line 1: ').strip()
            email = input('Enter admin email: ').strip().lower()
            first_name = input('Enter admin first name: ').strip()
            last_name = input('Enter admin last name: ').strip()
            self.stdout.write('Recommendation: For the public (principal) tenant, use domain "localhost".')
            domain_name = input('Enter domain (e.g., localhost or tenant.example.com): ').strip()
            generate_password = input('Generate random password? (y/n): ').strip().lower()

            if generate_password == 'y':
                password = self.generate_random_password()
                self.stdout.write(f'Generated password: {password}')
            else:
                password = input('Enter admin password: ').strip()

            # Validate inputs
            if not tenant_name or not schema_name or not email or not first_name or not last_name or not password:
                self.stderr.write('All fields are required.')
                return

            if Organisation.objects.filter(schema_name=schema_name).exists():
                self.stderr.write(f'Schema name "{schema_name}" already exists.')
                return

            if Organisation.objects.filter(name=tenant_name).exists():
                self.stderr.write(f'Tenant name "{tenant_name}" already exists.')
                return

            if User.objects.filter(email=email).exists():
                self.stderr.write(f'Email "{email}" is already in use.')
                return

        except KeyboardInterrupt:
            self.stderr.write('\nOperation cancelled by user.')
            return

        # Create tenant, user, and domain in a transaction
        try:
            with transaction.atomic():
                # Create Organisation (tenant)
                tenant = Organisation.objects.create(
                    schema_name=schema_name,
                    name=tenant_name,
                    quater=quater,
                    address_line1=address_line1,
                    approval_status=ApprovalStatusType.APPROVED,
                    is_active=True
                )
                self.stdout.write(f'Created tenant: {tenant_name} (schema: {schema_name})')

                # Run migrations for the tenant schema
                logger.info(f"Running migrations for schema {schema_name}")
                if not schema_exists(tenant.schema_name):
                    tenant.create_new_schema()
                call_command('migrate_schemas',
                             tenant=schema_name != settings.PUBLIC_SCHEMA_NAME,
                             schema_name=schema_name,
                             interactive=False)
                logger.info(f"Migrations completed for schema {schema_name}")
                self.stdout.write(f'Ran migrations for schema: {schema_name}')

                # Create user (admin)
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    approval_status=ApprovalStatusType.APPROVED,
                    is_active=True,
                    is_superuser=True,
                    is_staff=True
                )
                user.set_password(password)
                user.save()
                user.tenants.add(tenant)
                tenant.owner = user
                tenant.save()
                self.stdout.write(f'Created admin user: {email}')

                # Create Domain
                Domain.objects.create(
                    domain=domain_name,
                    tenant=tenant,
                    is_primary=True
                )
                self.stdout.write(f'Created domain: {domain_name}')

                # Assign user to appropriate group in tenant schema
                with schema_context(schema_name):
                    # Use POLYCAMPUS group for public schema, otherwise TENANT_ADMIN
                    group_name = UserGroupName.POLYCAMPUS if schema_name == 'public' else UserGroupName.TENANT_ADMIN
                    group, _ = Group.objects.get_or_create(name=group_name)
                    user_perm, _ = UserTenantPermissions.objects.get_or_create(
                        profile=user,
                        is_staff=True,
                        is_superuser=True,
                    )
                    user_perm.groups.add(group)
                    user_perm.save()
                    self.stdout.write(f'Assigned user to group: {group_name}')

                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created tenant "{tenant_name}", admin "{email}", and domain "{domain_name}"'
                ))

        except Exception as e:
            self.stderr.write(f'Error occurred: {str(e)}')
            self.stderr.write('Rolling back changes...')
            raise  # Let transaction.atomic handle the rollback
