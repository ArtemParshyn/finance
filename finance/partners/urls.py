from django.urls import path
from rest_framework.viewsets import ModelViewSet

from partners.views import ModelViewListCreatePartners, ModelViewRetrieveUpdateDestroyPartners, partners

urlpatterns = [
    path('partners', partners, name='partners'),
    path('api/', ModelViewListCreatePartners.as_view(), name='partners_api'),
    path('api/<int:pk>/', ModelViewRetrieveUpdateDestroyPartners.as_view())
]
