import json
from datetime import timedelta, datetime

from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, User
from .models import Payment, Partner


class LandingView(TemplateView):
    template_name = 'landing.html'


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email.split('@')[0]

            suffix = 1
            original_username = user.username
            while User.objects.filter(username=user.username).exists():
                user.username = f"{original_username}{suffix}"
                suffix += 1

            user.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Payment, Partner

import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Payment, Partner

import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .models import Payment, Partner


@login_required
def dashboard_view(request):
    today = timezone.now().date()

    # Генерация дат за последние 7 дней
    labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%d %b'))

    # Инициализация списка выручки нулями
    revenue_data = [0.0] * 7

    # Получаем агрегированные данные по оплаченным платежам
    payments = Payment.objects.filter(
        user=request.user,
        status='paid',
        date_paid__gte=today - timedelta(days=6),
        date_paid__lte=today
    ).values('date_paid').annotate(total=Sum('amount')).order_by('date_paid')

    # Заполняем данные для графика
    for payment in payments:
        days_diff = (today - payment['date_paid']).days
        index = 6 - days_diff
        if 0 <= index < 7:
            revenue_data[index] = float(payment['total'])

    # Рассчет процентного изменения выручки
    if len(revenue_data) >= 2:
        today_rev = revenue_data[6]
        yesterday_rev = revenue_data[5]

        if yesterday_rev > 0:
            revenue_change_percent = (today_rev - yesterday_rev) / yesterday_rev * 100
        else:
            revenue_change_percent = 100.0 if today_rev > 0 else 0.0
    else:
        revenue_change_percent = 0.0

    # Основные метрики
    total_revenue = Payment.objects.filter(
        user=request.user,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Успешные транзакции (оплаченные платежи)
    successful_transactions = Payment.objects.filter(
        user=request.user,
        status='paid'
    ).count()

    pending_invoices = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).count()

    # Сумма ожидающих платежей
    outstanding = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Последние транзакции
    recent_transactions = Payment.objects.filter(
        user=request.user
    ).select_related('client').order_by('-date_issued')[:5]

    # Рассчет финансового здоровья компании
    financial_score = 80  # базовый балл

    # Корректировки на основе показателей
    if total_revenue > 10000:
        financial_score += 10
    elif total_revenue > 5000:
        financial_score += 5

    if successful_transactions > 20:
        financial_score += 10
    elif successful_transactions > 10:
        financial_score += 5

    if pending_invoices > 5:
        financial_score -= 10
    elif pending_invoices > 3:
        financial_score -= 5

    # Ограничение до 100
    financial_score = min(max(financial_score, 0), 100)

    # Подготовка данных для графика
    chart_labels = json.dumps(labels)
    chart_data = json.dumps(revenue_data)

    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'revenue_change_percent': revenue_change_percent,
        'total_revenue': total_revenue,
        'successful_transactions': successful_transactions,
        'pending_invoices': pending_invoices,
        'outstanding': outstanding,
        'recent_transactions': recent_transactions,
        'financial_score': financial_score,
    }

    return render(request, 'dashboard.html', context)


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.company = request.POST.get('company', '')
        user.position = request.POST.get('position', '')
        user.address = request.POST.get('address', '')
        user.bio = request.POST.get('bio', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})