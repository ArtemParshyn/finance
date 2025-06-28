from rest_framework.serializers import ModelSerializer
from partners.models import Partner
from products.models import Product


class SerializerPartners(ModelSerializer):
    class Meta:
        model = Partner
        fields = (
            'id',
            'user',
            'name',
            'contact_person',
            'email',
            'phone',
            'address',
            'vat_code',
            'registration_number',
            'payment_terms',
            'created_at',
            'updated_at',
        )
