from decimal import Decimal

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from back.models import User
from invoice.models import Payment
from partners.models import Partner


class InvoiceSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    client = serializers.PrimaryKeyRelatedField(queryset=Partner.objects.all())
    invoice_number = serializers.CharField(max_length=20, validators=[UniqueValidator(queryset=Payment.objects.all())])
    items = serializers.JSONField(decoder=None, encoder=None, style={'base_template': 'textarea.html'})
    amount = serializers.DecimalField(decimal_places=2, max_digits=10, min_value=Decimal(0.01))
    date_issued = serializers.DateField()
    date_paid = serializers.DateField(required=False, allow_null=True)
    date_due = serializers.DateField()
    status = serializers.ChoiceField(
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')],
        required=False)
    description = serializers.CharField(allow_blank=True, required=False, style={'base_template': 'textarea.html'})

    def validate(self, data):
        """
        Переносим общую валидацию для create и update в этот метод
        """
        date_paid = data.get('date_paid')
        date_issued = data.get('date_issued')
        date_due = data.get('date_due')
        status_val = data.get('status')

        # Для случаев частичного обновления (PATCH) берем текущие значения
        if self.instance:
            if date_issued is None:
                date_issued = self.instance.date_issued
            if date_due is None:
                date_due = self.instance.date_due
            if status_val is None:
                status_val = self.instance.status

        # Проверка статуса 'paid'
        if status_val == 'paid' and not date_paid:
            raise serializers.ValidationError({
                "status": "Status 'paid' requires date_paid field"
            })

        # Проверка даты оплаты
        if date_paid and date_issued and date_paid < date_issued:
            raise serializers.ValidationError({
                "date_paid": "Payment date cannot be before issue date"
            })

        # Проверка даты выполнения
        if date_issued and date_due and date_issued > date_due:
            raise serializers.ValidationError({
                "date_issued": "Issue date cannot be after due date"
            })

        return data

    def create(self, validated_data):
        # Валидация теперь происходит в методе validate()
        return Payment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Обновляем все поля, а не только выборочные
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
