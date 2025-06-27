from datetime import datetime
from django.shortcuts import render, redirect
from rest_framework import generics
from back.models import User
from settings.models import InvoiceSettings
from settings.serializers import ModelSerializerCompany_User
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def invoice_settings_view(request):
    # Получаем или создаем настройки счетов
    settings, created = InvoiceSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        try:
            # Обновляем настройки счетов
            settings.prefix = request.POST.get('prefix', 'INV-')
            settings.next_number = int(request.POST.get('next_number', 1))
            settings.format = request.POST.get('format', 'sequential')
            settings.payment_terms = int(request.POST.get('payment_terms', 14))
            settings.currency = request.POST.get('currency', 'USD')
            settings.auto_increment = 'auto_increment' in request.POST
            settings.tax_included = 'tax_included' in request.POST
            settings.auto_reminders = 'auto_reminders' in request.POST
            settings.save()

            messages.success(request, 'Invoice settings updated successfully!')
            return redirect('invoice_settings')
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')

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
        'currencies': currencies,
        'current_year': now.year,
        'current_month': f"{now.month:02d}"  # Форматируем месяц с ведущим нулем
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


