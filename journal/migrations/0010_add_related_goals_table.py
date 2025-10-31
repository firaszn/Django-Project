# Manual migration to create journal_journal_related_goals table
from django.db import migrations


def create_table(apps, schema_editor):
    # Create the M2M table manually
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_journal_related_goals (
                id bigint AUTO_INCREMENT PRIMARY KEY,
                journal_id bigint NOT NULL,
                goal_id bigint NOT NULL,
                UNIQUE KEY unique_journal_goal (journal_id, goal_id),
                FOREIGN KEY (journal_id) REFERENCES journal_journal(id),
                FOREIGN KEY (goal_id) REFERENCES reminder_and_goals_goal(id)
            )
        """)


def drop_table(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS journal_journal_related_goals")


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0009_add_journalimage'),
        ('reminder_and_goals', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_table, drop_table),
    ]

