"""Placeholder migration to satisfy historic dependency.

Some merge migrations reference ('journal', '0002_journal_delete_journalentry').
This repository does not include that file (it was removed/merged). Add a no-op
migration so Django's migration graph can be built. If you have the original
migration contents, restore them here instead.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0001_initial"),
    ]

    operations = []
