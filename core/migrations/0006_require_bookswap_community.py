import django.db.models.deletion
from django.db import migrations, models


def delete_unscoped_swaps(apps, schema_editor):
    BookSwap = apps.get_model("core", "BookSwap")
    BookSwap.objects.filter(community__isnull=True).delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("core", "0005_bookswap_community"),
    ]

    operations = [
        migrations.RunPython(delete_unscoped_swaps, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bookswap",
            name="community",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="swaps",
                to="core.community",
            ),
        ),
    ]
