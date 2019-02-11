# Generated by Django 2.1.5 on 2019-02-11 13:13

from django.db import migrations

def criar_parametro_inicial(apps, schema_editor):
    ParameterForUser = apps.get_model('core', 'ParametersUser')
    parametro = ParameterForUser.objects.first()

    if not parametro:
        parametro = ParameterForUser()
        parametro.senha_padrao = "password@123456"
        parametro.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_parametersuser'),
    ]

    operations = [
        migrations.RunPython(criar_parametro_inicial)
    ]