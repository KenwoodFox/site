from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kitsunerobotics", "0002_articletags"),
    ]

    operations = [
        migrations.AddField(
            model_name="articletags",
            name="preview",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
