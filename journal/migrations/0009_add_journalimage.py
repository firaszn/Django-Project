# Generated manually to add missing JournalImage table

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0008_alter_journal_is_public'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='journal_images/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='journal.journal')),
            ],
        ),
    ]

