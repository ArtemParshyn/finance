from datetime import datetime
from django.shortcuts import render, redirect
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from back.models import User
from settings.models import InvoiceSettings, NumberingTemplate
from settings.serializers import ModelSerializerCompany_User, NumberingTemplateSerializer, InvoiceSettingsSerializer
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def invoice_settings_view(request):
    # Получаем настройки и шаблоны
    settings = InvoiceSettings.objects.get_or_create(user=request.user)[0]
    templates = NumberingTemplate.objects.filter(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # Обработка общих настроек
        if form_type == 'general':
            try:
                settings.payment_terms = int(request.POST.get('payment_terms', 14))
                settings.currency = request.POST.get('currency', 'USD')
                settings.tax_included = 'tax_included' in request.POST
                settings.auto_reminders = 'auto_reminders' in request.POST
                settings.save()
                messages.success(request, 'Invoice settings updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating settings: {str(e)}')

        # Обработка шаблонов нумерации
        elif form_type == 'template':
            try:
                template_id = request.POST.get('template_id')

                if template_id:
                    # Редактирование существующего шаблона
                    template = get_object_or_404(
                        NumberingTemplate,
                        id=template_id,
                        user=request.user
                    )
                else:
                    # Создание нового шаблона
                    template = NumberingTemplate(user=request.user)

                # Обновление данных шаблона
                template.name = request.POST.get('name')
                template.prefix = request.POST.get('prefix')
                template.next_number = int(request.POST.get('next_number', 1))
                template.format = request.POST.get('format')
                template.custom_format = request.POST.get('custom_format', '')

                # Обработка флага "по умолчанию"
                if 'is_default' in request.POST:
                    # Сброс предыдущего шаблона по умолчанию
                    NumberingTemplate.objects.filter(
                        user=request.user,
                        is_default=True
                    ).update(is_default=False)
                    template.is_default = True
                else:
                    template.is_default = False

                template.save()
                messages.success(request, 'Template saved successfully!')
            except Exception as e:
                messages.error(request, f'Error saving template: {str(e)}')

        elif form_type == 'delete_template':
            try:
                template_id = request.POST.get('template_id')
                template = get_object_or_404(
                    NumberingTemplate,
                    id=template_id,
                    user=request.user
                )
                template.delete()
                messages.success(request, 'Template deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting template: {str(e)}')
        return redirect('settings')

    # Подготовка данных для шаблона
    currencies = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('CHF', 'Swiss Franc'),
        ('CNY', 'Chinese Yuan'),
        ('INR', 'Indian Rupee'),
        ('MXN', 'Mexican Peso'),
    ]

    # Получаем текущий год и месяц для шаблона
    now = datetime.now()
    return render(request, 'settings.html', {
        'invoice_settings': settings,
        'numbering_templates': templates,
        'currencies': currencies,
        'current_year': now.year,
        'current_month': f"{now.month:02d}"
    })

@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        try:
            # Обновляем основные поля
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.phone = request.POST.get('phone', '')

            # Обновляем информацию о компании
            user.company = request.POST.get('company', '')
            user.company_type = request.POST.get('company_type', 'individual')
            user.position = request.POST.get('position', '')
            user.address = request.POST.get('address', '')

            # Обновляем финансовую информацию
            user.vat_code = request.POST.get('vat_code', '')
            user.registration_number = request.POST.get('registration_number', '')
            user.bank_name = request.POST.get('bank_name', '')
            user.bank_account = request.POST.get('bank_account', '')
            user.bic = request.POST.get('bic', '')

            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    return render(request, 'profile.html', {'user': user})


class ModelViewCompany_User(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ModelSerializerCompany_User

    def get_object(self):
        return self.request.user


class InvoiceSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSettingsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']

    def get_queryset(self):
        return InvoiceSettings.objects.filter(user=self.request.user)

    def get_object(self):
        return get_object_or_404(InvoiceSettings, user=self.request.user)

    def create(self, request):
        # Уже создается через сигнал
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class NumberingTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = NumberingTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NumberingTemplate.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        template = self.get_object()
        # Сброс предыдущего шаблона по умолчанию
        NumberingTemplate.objects.filter(
            user=request.user,
            is_default=True
        ).exclude(id=template.id).update(is_default=False)

        template.is_default = True
        template.save()
        return Response({'status': 'default template set'})