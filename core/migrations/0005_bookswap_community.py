from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_communitymembershiprequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookswap",
            name="community",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="swaps",
                to="core.community",
            ),
        ),
    ]
