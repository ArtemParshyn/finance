import django.utils.timezone
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)

    # Дополнительные поля
    COMPANY_TYPE_CHOICES = [
        ('individual', _('Individual')),
        ('company', _('Company')),
    ]

    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    company = models.CharField(_('Company'), max_length=100, blank=True)
    company_type = models.CharField(
        _('Company Type'),
        max_length=20,
        choices=COMPANY_TYPE_CHOICES,
        default='individual'
    )
    position = models.CharField(_('Position'), max_length=100, blank=True)
    address = models.TextField(_('Address'), blank=True)
    bio = models.TextField(_('Bio'), blank=True)
    email_verified = models.BooleanField(_('Email Verified'), default=False)

    # Добавленные поля для PDF счета
    vat_code = models.CharField(
        _('VAT Code'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Tax identification number (VAT code)')
    )
    bank_name = models.CharField(
        _('Bank Name'),
        max_length=100,
        blank=True,
        null=True
    )
    bank_account = models.CharField(
        _('Bank Account'),
        max_length=50,
        blank=True,
        null=True
    )
    bic = models.CharField(
        _('BIC/SWIFT'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Bank Identifier Code')
    )
    registration_number = models.CharField(
        _('Registration Number'),
        max_length=50,
        blank=True,
        null=True
    )

    # Устанавливаем email как поле для входа
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


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
