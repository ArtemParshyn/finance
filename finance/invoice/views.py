from rest_framework import status
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from settings.models import InvoiceSettings
from .models import Payment
from .serializers import InvoiceSerializer
from datetime import datetime
from django.db import transaction


def generate_invoice_number(settings):
    """Генерирует номер счета на основе настроек"""
    if settings.format == 'sequential':
        return f"{settings.prefix}{settings.next_number:06d}"
    elif settings.format == 'year':
        year = datetime.now().year
        return f"{settings.prefix}{year}-{settings.next_number:04d}"
    elif settings.format == 'month':
        month = datetime.now().strftime('%Y%m')
        return f"{settings.prefix}{month}-{settings.next_number:04d}"
    # Добавляем fallback на случай неизвестного формата
    return f"{settings.prefix}{settings.next_number:06d}"


class InvoiceView(RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = InvoiceSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем платежи текущего пользователя
        return super().get_queryset().filter(user=self.request.user)


class InvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


    def get(self, request):
        # Возвращаем платежи только текущего пользователя
        payments = Payment.objects.filter(user=request.user)
        serializer = InvoiceSerializer(payments, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        # Получаем настройки счетов пользователя
        settings = InvoiceSettings.objects.get_or_create(user=request.user)[0]

        # Генерируем номер счета
        invoice_number = generate_invoice_number(settings)

        # Устанавливаем номер счета и пользователя
        data['invoice_number'] = invoice_number
        data['user'] = request.user.id

        # Создаем платеж
        serializer = InvoiceSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            payment = serializer.save()

            # Увеличиваем номер счета если включен автоинкремент
            if settings.auto_increment:
                settings.next_number += 1
                settings.save()

        return Response(
            InvoiceSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

    def put(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(
            Payment,
            id=pk,
            user=request.user  # Фильтрация по пользователю
        )

        # Обновление платежа
        serializer = InvoiceSerializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_payment = serializer.save()

        return Response(
            InvoiceSerializer(updated_payment).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(
            Payment,
            id=pk,
            user=request.user  # Фильтрация по пользователю
        )

        instance.delete()
        return Response(
            {"message": "Payment deleted successfully"},
            status=status.HTTP_200_OK
        )