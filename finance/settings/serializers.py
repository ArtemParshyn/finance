from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from back.models import User
from settings.models import InvoiceSettings, NumberingTemplate


class ModelSerializerCompany_User(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'vat_code',
            'registration_number',
            'bic',
            'bank_account',
            'company',
            'company_type',
            'bank_name',
            'bank_account',
            'bic',
            'registration_number'
        )


from rest_framework import serializers
from .models import InvoiceSettings, NumberingTemplate


class NumberingTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberingTemplate
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate(self, data):
        if data.get('format') == 'custom' and not data.get('custom_format'):
            raise serializers.ValidationError("Custom format is required for custom templates")
        return data


class InvoiceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceSettings
        fields = '__all__'
        read_only_fields = ('user', 'last_updated')