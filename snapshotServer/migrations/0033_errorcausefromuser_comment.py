from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "snapshotServer",
            "0032_alter_error_relatederrors",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="errorcausefromuser",
            name="errorMessage",
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name="errorcausefromuser",
            name="comment",
            field=models.CharField(
                default="",
                max_length=1000,
            ),
        ),
    ]