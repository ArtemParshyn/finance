from rest_framework import status
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from settings.models import NumberingTemplate
from .models import Payment
from .serializers import InvoiceSerializer
from django.db import transaction


class InvoiceView(RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = InvoiceSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class InvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        user = request.user

        template_id = data.pop('template_id', [None])[0] if 'template_id' in data else None
        if template_id:
            template = get_object_or_404(
                NumberingTemplate,
                id=template_id,
                user=user
            )
        else:
            template = NumberingTemplate.objects.filter(
                user=user,
                is_default=True
            ).first() or NumberingTemplate(
                user=user,
                name="Temporary",
                format='sequential',
                prefix='INV-'
            )

        invoice_number = template.generate_number()
        data['invoice_number'] = invoice_number
        data['user'] = user.id

        serializer = InvoiceSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            payment = serializer.save()
            if template.pk:
                template.next_number += 1
                template.save()

        return Response(
            InvoiceSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

    def get(self, request):
        payments = Payment.objects.filter(user=request.user)
        serializer = InvoiceSerializer(payments, many=True)
        return Response(serializer.data)





    def put(self, request, pk=None):
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(Payment, id=pk, user=request.user)
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

    def delete(self, request, pk=None):
        if not pk:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        instance = get_object_or_404(Payment, id=pk, user=request.user)
        instance.delete()
        return Response(
            {"message": "Payment deleted successfully"},
            status=status.HTTP_200_OK
        )