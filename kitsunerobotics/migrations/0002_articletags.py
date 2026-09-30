import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kitsunerobotics", "0001_initial"),
        ("siteblog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArticleTags",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("names", models.JSONField(blank=True, default=list)),
                (
                    "article",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="article_tags",
                        to="siteblog.article",
                    ),
                ),
            ],
            options={
                "verbose_name": "Article tags",
                "verbose_name_plural": "Article tags",
            },
        ),
    ]
