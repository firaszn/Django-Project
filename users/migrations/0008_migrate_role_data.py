# Generated migration for data migration

from django.db import migrations


def migrate_role_from_is_staff(apps, schema_editor):
    """Migrate existing is_staff/is_superuser to role field"""
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Set role='admin' for staff users
    CustomUser.objects.filter(is_staff=True).update(role='admin')
    
    # Set role='user' for non-staff users
    CustomUser.objects.filter(is_staff=False).update(role='user')


def reverse_migrate_role(apps, schema_editor):
    """Reverse migration - convert role back to is_staff"""
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Set is_staff=True for admin users
    for user in CustomUser.objects.filter(role='admin'):
        user.is_staff = True
        user.is_superuser = True
        user.save()
    
    # Set is_staff=False for regular users
    for user in CustomUser.objects.filter(role='user'):
        user.is_staff = False
        user.is_superuser = False
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_add_role_field'),
    ]

    operations = [
        migrations.RunPython(migrate_role_from_is_staff, reverse_migrate_role),
    ]

