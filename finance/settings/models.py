from django.db import models
from django.core.exceptions import ValidationError
from back.models import User
from datetime import datetime
import re


class NumberingTemplate(models.Model):
    FORMAT_CHOICES = [
        ('sequential', 'Sequential Numbering'),
        ('year', 'Year-based Numbering'),
        ('month', 'Month-based Numbering'),
        ('custom', 'Custom Format'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='numbering_templates')
    name = models.CharField(max_length=100, help_text="Template name (e.g., 'Services', 'Products')")
    prefix = models.CharField(max_length=20, default='INV-')
    next_number = models.PositiveIntegerField(default=1)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='sequential')
    custom_format = models.CharField(
        max_length=100,
        blank=True,
        help_text="Use placeholders: {year}, {month}, {day}, {seq}. Example: 'INV-{year}-{seq:05d}'"
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.format == 'custom':
            if not self.custom_format:
                raise ValidationError("Custom format is required for custom templates")

            # Проверка наличия обязательного плейсхолдера {seq}
            if '{seq}' not in self.custom_format:
                raise ValidationError("Custom format must include {seq} placeholder")

            # Проверка допустимых плейсхолдеров
            valid_placeholders = {'year', 'month', 'day', 'seq'}
            placeholders = re.findall(r'\{(\w+)(?::[^\}]*)?\}', self.custom_format)
            for ph in placeholders:
                if ph not in valid_placeholders:
                    raise ValidationError(f"Invalid placeholder: {ph}. Allowed: {', '.join(valid_placeholders)}")

    def save(self, *args, **kwargs):
        self.clean()
        if self.is_default:
            # Сбрасываем default у других шаблонов пользователя
            NumberingTemplate.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def generate_number(self):
        now = datetime.now()
        seq = self.next_number

        if self.format == 'sequential':
            return f"{self.prefix}{seq:06d}"
        elif self.format == 'year':
            return f"{self.prefix}{now.year}-{seq:04d}"
        elif self.format == 'month':
            return f"{self.prefix}{now.year}{now.month:02d}-{seq:04d}"
        elif self.format == 'custom' and self.custom_format:
            return self.custom_format.format(
                year=now.year,
                month=now.month,
                day=now.day,
                seq=seq
            )
        return f"{self.prefix}{seq:06d}"  # Fallback

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class InvoiceSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='invoice_settings')
    payment_terms = models.PositiveSmallIntegerField(default=14)  # days
    currency = models.CharField(max_length=3, default='USD')
    tax_included = models.BooleanField(default=False)
    auto_reminders = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Invoice Settings"

    def __str__(self):
        return f"Invoice Settings ({self.user.email})"