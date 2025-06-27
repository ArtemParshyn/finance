from django.utils.translation import gettext_lazy as _

from django.core.validators import MinValueValidator
from django.db import models

from back.models import User, Partner


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='payments')
    invoice_number = models.CharField(_('invoice number'), max_length=20, unique=True)
    items = models.JSONField(null=False, blank=False)
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    date_issued = models.DateField(_('date issued'))
    date_due = models.DateField(_('date due'))
    date_paid = models.DateField(_('date paid'), null=True, blank=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        blank=True
    )
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"

    class Meta:
        ordering = ['-date_issued']
