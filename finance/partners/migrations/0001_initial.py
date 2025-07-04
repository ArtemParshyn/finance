# Generated by Django 4.2 on 2025-06-27 20:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('contact_person', models.CharField(max_length=100, verbose_name='contact person')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('phone', models.CharField(max_length=20, verbose_name='phone')),
                ('address', models.TextField(blank=True, verbose_name='address')),
                ('vat_code', models.CharField(blank=True, help_text='Tax identification number (VAT code)', max_length=50, null=True, verbose_name='VAT Code')),
                ('registration_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='Registration Number')),
                ('payment_terms', models.TextField(blank=True, help_text='Default payment terms for invoices', null=True, verbose_name='Payment Terms')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partners', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
