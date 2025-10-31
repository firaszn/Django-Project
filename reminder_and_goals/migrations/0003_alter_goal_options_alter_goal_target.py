"""Placeholder migration to satisfy historic dependency for reminder_and_goals.

Some later migrations reference ('reminder_and_goals', '0003_alter_goal_options_alter_goal_target')
but the original migration is missing. Add a no-op placeholder to allow the migration
graph to be built. Replace with the original migration contents if available.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reminder_and_goals", "0002_initial"),
    ]

    operations = []
