"""Placeholder migration to satisfy historic dependency for TagsCat.

Some migrations reference ('TagsCat', '0002_category_tags') but the original
file isn't present in the repository. This no-op migration allows Django to build
the migration graph. If you have the original migration, restore it instead.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("TagsCat", "0001_initial"),
    ]

    operations = []
