from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scanner_api", "0002_alter_scanresult_client"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="scan_requested",
            field=models.BooleanField(default=False),
        ),
    ]
