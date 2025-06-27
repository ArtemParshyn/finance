from rest_framework import status, serializers
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from invoice.models import Payment
from invoice.serializers import InvoiceSerializer


class InvoiceView(RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = InvoiceSerializer
    lookup_field = 'pk'  # Указываем, что 'id' используется как параметр

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class InvoiceAPIView(APIView):
    queryset = Payment.objects.all()
    serializer = InvoiceSerializer

    def get(self, request):
        print(request.user)
        return Response(status=status.HTTP_200_OK, data=self.queryset.values())

    def post(self, request):
        data = request.data
        print(data)
        data.update({'user': 1})
        payment = self.serializer(data=data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(Payment, id=pk)

        # Добавляем partial=True для частичного обновления
        payment = InvoiceSerializer(instance=instance, data=request.data, partial=True)
        payment.is_valid(raise_exception=True)
        updated_payment = payment.save()  # Сохраняем изменения

        # Возвращаем обновленные данные
        return Response(status=status.HTTP_200_OK, data=InvoiceSerializer(updated_payment).data)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(Payment, id=pk)

        instance.delete()

        # Возвращаем обновленные данные
        return Response(status=status.HTTP_200_OK, data={"message": "deleted"})
