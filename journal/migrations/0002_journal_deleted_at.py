from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='When this entry was moved to the trash', null=True),
        ),
    ]
