from rest_framework.serializers import ModelSerializer

from back.models import User


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