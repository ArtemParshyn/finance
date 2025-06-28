from django.db import models
from django.utils.translation import gettext_lazy as _
from back.models import User


class Partner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partners')
    name = models.CharField(_('name'), max_length=100)
    contact_person = models.CharField(_('contact person'), max_length=100)
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=20)
    address = models.TextField(_('address'), blank=True)

    # Добавленные поля для PDF счета
    vat_code = models.CharField(
        _('VAT Code'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Tax identification number (VAT code)')
    )
    registration_number = models.CharField(
        _('Registration Number'),
        max_length=50,
        blank=True,
        null=True
    )
    payment_terms = models.TextField(
        _('Payment Terms'),
        blank=True,
        null=True,
        help_text=_('Default payment terms for invoices')
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    def __str__(self):
        return self.name
