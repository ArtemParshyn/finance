from django.urls import path

from invoice.views import InvoiceAPIView, InvoiceView

urlpatterns = [
    path('api/', InvoiceAPIView.as_view()),
    path('api/<int:pk>/', InvoiceAPIView.as_view()),
    path('api/payment/<int:pk>', InvoiceView.as_view())
]
