from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import login, logout
from django.contrib import messages
import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from invoice.models import Payment
from partners.models import Partner
from .forms import CustomUserCreationForm, CustomAuthenticationForm, User

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import locale
from num2words import num2words
from datetime import datetime


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


@login_required
def payments(request):
    payments = Payment.objects.all().filter(user=request.user).order_by('-date_issued')
    clients = Partner.objects.all().filter(user=request.user)  # Получаем всех клиентов

    # Пагинация
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'payments.html', {
        'payments': page_obj,
        'clients': clients  # Передаем клиентов в контекст
    })


from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import locale
from num2words import num2words
from datetime import datetime
from django.utils import timezone

import os
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from num2words import num2words
from django.contrib.auth.decorators import login_required
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from invoice.models import Payment
from django.utils.translation import gettext_lazy as _


@login_required
def register_support_fonts(request):
    try:
        # Попробуем найти шрифт в нескольких местах
        font_locations = [
            # Windows
            r'C:\W1indows\Fonts\arialuni.ttf',  # Arial Unicode MS
            r'C:\Windows\Fonts\times.ttf',  # Times New Roman

            # Linux
            '/usr/share/fonts/truetype/dejavu/Deja1VuSans.ttf',
            '/usr/share/fonts/truetype/liberation/Liberat1ionSans-Regular.ttf',

            # MacOS
            '/Library/Fonts/Arial Unic1ode.ttf',

            # В проекте
            os.path.join(os.path.dirname(__file__), 'static/fonts/D1ejaVuSans.ttf'),
            os.path.join(os.path.dirname(__file__), 'static/fonts/A1rialUnicode.ttf'),
        ]
        print(os.path.join(os.path.dirname(__file__), 'static/fonts/A1rialUnicode.ttf'),)

        for font_path in font_locations:
            if os.path.exists(font_path):
                print(font_path)
                font_name = os.path.splitext(os.path.basename(font_path))[0]
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    # Регистрируем жирную версию если есть
                    bold_path = font_path.replace('.ttf', '-Bold.ttf')
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont(f'{font_name}-Bold', bold_path))
                    return font_name
                except:
                    continue

        # Если ничего не найдено, используем стандартный шрифт
        return 'Helvetica'
    except Exception as e:
        print(f"Error registering fonts: {e}")
        return 'Helvetica'


@login_required
def generate_invoice_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    client = payment.client

    # Регистрируем шрифты
    support_font = register_support_fonts(request)

    # Создаем буфер для PDF
    buffer = BytesIO()

    # Настройки документа
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=f"Sąskaita faktūra {payment.invoice_number}"
    )

    # Стили
    styles = getSampleStyleSheet()

    # Основные стили
    style_heading = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=5,
        fontName=f'{support_font}-Bold' if support_font != 'Helvetica' else 'Helvetica-Bold'
    )

    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=3,
        fontName=support_font
    )

    style_bold = ParagraphStyle(
        'Bold',
        parent=style_normal,
        fontName=f'{support_font}-Bold' if support_font != 'Helvetica' else 'Helvetica-Bold'
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=style_normal,
        fontName=f'{support_font}-Bold' if support_font != 'Helvetica' else 'Helvetica-Bold',
        fontSize=9,
        alignment=TA_CENTER
    )

    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=style_normal,
        fontSize=9
    )

    style_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=style_table_cell,
        alignment=TA_CENTER
    )

    style_table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=style_table_cell,
        alignment=TA_RIGHT
    )

    # Функция форматирования валюты
    def format_currency(value):
        try:
            value = float(value)
            return f"{value:,.2f}".replace(",", " ").replace(".", ",")
        except:
            return "0,00"

    # Формируем документ
    story = []

    # 1. Заголовок
    story.append(Paragraph("SĄSKAITA FAKTŪRA", style_heading))
    story.append(Spacer(1, 10))

    # 2. Номер и дата
    story.append(Paragraph(f"<b>Serija ir Nr.:</b> {payment.invoice_number}", style_normal))
    story.append(Paragraph(f"<b>Išrašymo data:</b> {payment.date_issued.strftime('%Y m. %B %d d.')}", style_normal))
    story.append(Spacer(1, 15))

    # 3. Продавец и покупатель
    story.append(Paragraph("<b>Pardavėjas</b>", style_bold))
    seller_info = []
    seller_info.append(request.user.company or request.user.get_full_name())
    if request.user.registration_number:
        seller_info.append(f"Įmonės kodas: {request.user.registration_number}")
    if request.user.address:
        seller_info.append(f"Adresas: {request.user.address}")

    for line in seller_info:
        story.append(Paragraph(line, style_normal))

    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>Pirkėjas</b>", style_bold))
    if client:
        buyer_info = []
        buyer_info.append(client.name)
        if client.address:
            buyer_info.append(f"Adresas: {client.address}")

        for line in buyer_info:
            story.append(Paragraph(line, style_normal))
    else:
        story.append(Paragraph("Nenurodytas", style_normal))

    story.append(Spacer(1, 15))

    # 4. Таблица товаров
    # Заголовки таблицы
    table_data = [
        [
            Paragraph("Pavadinimas", style_table_header),
            Paragraph("Kiekis", style_table_header),
            Paragraph("Matas", style_table_header),
            Paragraph("Kaina", style_table_header),
            Paragraph("Suma", style_table_header),
        ]
    ]

    # Товары
    for item in payment.items:
        name = item.get('name', '')
        quantity = item.get('quantity', 1)
        unit = item.get('unit', '')
        price = item.get('price', 0)
        total = item.get('total', 0)

        table_data.append([
            Paragraph(name, style_table_cell),
            Paragraph(str(quantity), style_table_cell_center),
            Paragraph(unit, style_table_cell_center),
            Paragraph(format_currency(price), style_table_cell_right),
            Paragraph(format_currency(total), style_table_cell_right),
        ])

    # Создаем таблицу
    items_table = Table(
        table_data,
        colWidths=[70 * mm, 20 * mm, 20 * mm, 30 * mm, 30 * mm]
    )

    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 10))

    # 5. Итоговые суммы
    total_amount = float(payment.amount)

    # Строка с промежуточной суммой
    story.append(Paragraph(
        f"Tarpinė suma (EUR): {format_currency(total_amount)}",
        style_table_cell_right
    ))

    # Строка с общей суммой
    story.append(Paragraph(
        f"Bendra suma (EUR): {format_currency(total_amount)}",
        style_table_cell_right
    ))

    story.append(Spacer(1, 10))

    # 6. Сумма прописью
    try:
        amount_in_words = num2words(
            total_amount,
            lang='lt',
            to='currency',
            currency='EUR'
        ).capitalize().replace('eurai', 'Eur').replace('euro', 'Eur')

        story.append(Paragraph(
            f"Suma žodžiais: {amount_in_words}",
            style_normal
        ))
    except Exception as e:
        print(f"Error converting amount to words: {e}")

    story.append(Spacer(1, 10))

    # 7. Срок оплаты
    story.append(Paragraph(
        f"Apmokėti iki: {payment.date_due.strftime('%Y-%m-%d')}",
        style_normal
    ))

    # Генерируем PDF
    doc.build(story)

    # Возвращаем PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=saskaita_{payment.invoice_number}.pdf'
    return response

def profile(request):
    return render(request, template_name='profile.html')
