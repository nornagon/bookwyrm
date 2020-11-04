# Generated by Django 3.0.7 on 2020-11-04 18:15

from django.db import migrations, models
import django.db.models.deletion


def set_default_edition(app_registry, schema_editor):
    db_alias = schema_editor.connection.alias
    works = app_registry.get_model('bookwyrm', 'Work').objects.using(db_alias)
    editions = app_registry.get_model('bookwyrm', 'Edition').objects.using(db_alias)
    for work in works:
        ed = editions.filter(parent_work=work, default=True).first()
        if not ed:
            ed = editions.filter(parent_work=work).first()
        work.default_edition = ed
        work.save()

class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0007_auto_20201103_0014'),
    ]

    operations = [
        migrations.AddField(
            model_name='work',
            name='default_edition',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='bookwyrm.Edition'),
        ),
        migrations.RunPython(set_default_edition),
        migrations.RemoveField(
            model_name='edition',
            name='default',
        ),
    ]
