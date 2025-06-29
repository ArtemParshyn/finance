from django.urls import path

from invoice.views import InvoiceAPIView, InvoiceView
from settings.views import NumberingTemplateViewSet

urlpatterns = [
    path('api/', InvoiceAPIView.as_view(), name='invoice-list'),
    path('api/<int:pk>/', InvoiceAPIView.as_view(), name='invoice-detail'),
    path('api/payment/<int:pk>', InvoiceView.as_view(), name='invoice-retrieve'),
]
