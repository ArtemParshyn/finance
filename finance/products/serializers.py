from rest_framework.serializers import ModelSerializer
from partners.models import Partner
from products.models import Product


class SerializerProducts(ModelSerializer):
    class Meta:
        model = Product

        fields = (
            'id',
            'user',
            'name',
            'description',
            'price',
            'unit',
            'vat_rate',
            'created_at',
            'updated_at',
        )
