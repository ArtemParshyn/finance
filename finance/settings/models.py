# models.py
from django.db import models

from back.models import User


class InvoiceSettings(models.Model):
    FORMAT_CHOICES = [
        ('sequential', 'Sequential Numbering'),
        ('year', 'Year-based Numbering'),
        ('month', 'Month-based Numbering'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    prefix = models.CharField(max_length=20, default='INV-')
    next_number = models.PositiveIntegerField(default=1)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='sequential')
    payment_terms = models.PositiveSmallIntegerField(default=14)  # days
    currency = models.CharField(max_length=3, default='USD')
    auto_increment = models.BooleanField(default=True)
    tax_included = models.BooleanField(default=False)
    auto_reminders = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Invoice Settings"

    def __str__(self):
        return f"Invoice Settings (Last updated: {self.last_updated})"

    def generate_next_number(self):
        """Generate the next invoice number based on settings"""
        if self.format == 'sequential':
            return f"{self.prefix}{self.next_number:06d}"
        elif self.format == 'year':
            from datetime import datetime
            year = datetime.now().strftime('%Y')
            return f"{self.prefix}{year}-{self.next_number:04d}"
        elif self.format == 'month':
            from datetime import datetime
            month = datetime.now().strftime('%Y%m')
            return f"{self.prefix}{month}-{self.next_number:04d}"

    def increment_number(self):
        """Increment the invoice number and save"""
        self.next_number += 1
        self.save()
