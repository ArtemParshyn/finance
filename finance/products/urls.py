from django.urls import path
from rest_framework.viewsets import ModelViewSet

from partners.views import ModelViewListCreatePartners, ModelViewRetrieveUpdateDestroyPartners, partners
from products.views import products, ModelViewListCreateProducts, ModelViewRetrieveUpdateDestroyProducts

urlpatterns = [
    path('products', products, name='products'),
    path('api/', ModelViewListCreateProducts.as_view(), name='partners_api'),
    path('api/<int:pk>/', ModelViewRetrieveUpdateDestroyProducts.as_view())
]
