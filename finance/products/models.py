from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from back.models import User


# Create your models here.
class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(_('Product Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit = models.CharField(_('Unit'), max_length=50, default='pcs')
    vat_rate = models.DecimalField(
        _('VAT Rate (%)'),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    def __str__(self):
        return self.name
