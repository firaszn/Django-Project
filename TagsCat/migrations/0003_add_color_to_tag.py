# Generated manually to add missing color field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TagsCat', '0002_category_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='color',
            field=models.CharField(blank=True, help_text='Hex color code (auto-generated if empty)', max_length=7),
        ),
    ]

