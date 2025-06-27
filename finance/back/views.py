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
from .forms import CustomUserCreationForm, CustomAuthenticationForm, User
from .models import Partner
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
    payments = Payment.objects.all().order_by('-date_issued')
    clients = Partner.objects.all()  # Получаем всех клиентов

    # Пагинация
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'payments.html', {
        'payments': page_obj,
        'clients': clients  # Передаем клиентов в контекст
    })



def generate_invoice_pdf(request, payment_id):
    """Генерирует PDF-счет на основе модели Payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except:
        pass

    seller = request.user
    buyer = payment.client

    invoice_date = payment.date_issued.strftime("%Y-%m-%d")
    due_date = payment.date_due.strftime("%Y-%m-%d")

    items = []
    subtotal_excl_vat = 0
    vat_sum = 0
    discount_total = 0

    for item in payment.items:
        unit_price = item.get('unit_price', 0)
        quantity = item.get('quantity', 1)
        discount = item.get('discount', 0)  # Процентная скидка
        vat_rate = item.get('vat', 21)  # Процент НДС

        # Расчеты с учетом скидки и НДС
        total_before_discount = unit_price * quantity
        discount_amount = total_before_discount * (discount / 100)
        total_after_discount = total_before_discount - discount_amount
        vat_amount = total_after_discount * (vat_rate / 100)
        total_incl_vat = total_after_discount + vat_amount

        items.append({
            "description": item.get('name', 'Service'),
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount,
            "vat_rate": vat_rate,
            "amount": total_incl_vat
        })

        subtotal_excl_vat += total_after_discount
        vat_sum += vat_amount
        discount_total += discount_amount

    grand_total = subtotal_excl_vat + vat_sum

    # Формирование суммы прописью
    try:
        amount_in_words = num2words(grand_total, to='currency', currency='EUR')
    except:
        amount_in_words = f"{grand_total:.2f} EUR"

    # Формируем данные для PDF
    invoice_data = {
        "invoice_number": payment.invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "seller": {
            "name": seller.get_full_name() or seller.username,
            "company": seller.company or "N/A",
            "address": seller.address or "N/A",
            "vat_code": seller.vat_code or "N/A",
            "bank_name": seller.bank_name or "N/A",
            "bank_account": seller.bank_account or "N/A",
            "bic": seller.bic or "N/A",
            "registration_number": seller.registration_number or "N/A",
        },
        "buyer": {
            "name": buyer.name,
            "contact_person": buyer.contact_person or "N/A",
            "address": buyer.address or "N/A",
            "vat_code": buyer.vat_code or "N/A",
            "registration_number": buyer.registration_number or "N/A",
        },
        "items": items,
        "subtotal_excl_vat": subtotal_excl_vat,
        "vat_sum": vat_sum,
        "discount_total": discount_total,
        "grand_total": grand_total,
        "currency": "EUR",
        "amount_in_words": amount_in_words,
        "invoiced_by":  seller.last_name+seller.first_name,
        "notes": payment.description or "No notes",
    }
    print(seller.first_name)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    # Добавляем кастомные стили
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=10 * mm
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=5 * mm
    ))

    styles.add(ParagraphStyle(
        name='CompanyHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=TA_LEFT,
    ))

    elements = []

    elements.append(Paragraph("INVOICE", styles['InvoiceTitle']))

    # Информация о счете
    invoice_info = [
        [Paragraph(f"<b>Invoice #:</b> {invoice_data['invoice_number']}", styles['Normal']),
         Paragraph(f"<b>Date:</b> {invoice_data['invoice_date']}", styles['Normal'])],
        [Paragraph(f"<b>Due Date:</b> {invoice_data['due_date']}", styles['Normal']), ""]
    ]

    invoice_table = Table(invoice_info, colWidths=[90 * mm, 90 * mm])
    elements.append(invoice_table)
    elements.append(Spacer(1, 10 * mm))

    # Продавец и покупатель
    seller_data = [
        [Paragraph("<b>From:</b>", styles['CompanyHeader'])],
        [Paragraph(invoice_data['seller']['name'], styles['Normal'])],
        [Paragraph(invoice_data['seller']['company'], styles['Normal'])],
        [Paragraph(f"VAT: {invoice_data['seller']['vat_code']}", styles['Normal'])],
        [Paragraph(f"Bank: {invoice_data['seller']['bank_name']}", styles['Normal'])],
        [Paragraph(f"Account: {invoice_data['seller']['bank_account']}", styles['Normal'])],
        [Paragraph(f"BIC: {invoice_data['seller']['bic']}", styles['Normal'])],
        [Paragraph(f"Reg. No: {invoice_data['seller']['registration_number']}", styles['Normal'])],
    ]

    buyer_data = [
        [Paragraph("<b>To:</b>", styles['CompanyHeader'])],
        [Paragraph(invoice_data['buyer']['name'], styles['Normal'])],
        [Paragraph(invoice_data['buyer']['address'], styles['Normal'])],
        [Paragraph(f"VAT: {invoice_data['buyer']['vat_code']}", styles['Normal'])],
        [Paragraph(f"Reg. No: {invoice_data['buyer']['registration_number']}", styles['Normal'])],
    ]

    seller_buyer_data = [
        [Table(seller_data), Table(buyer_data)]
    ]

    seller_buyer_table = Table(seller_buyer_data, colWidths=[90 * mm, 90 * mm])
    elements.append(seller_buyer_table)
    elements.append(Spacer(1, 10 * mm))

    # Таблица с товарами
    table_data = [
        [
            Paragraph("Description", styles['SectionHeader']),
            Paragraph("Qty", styles['SectionHeader']),
            Paragraph("Unit Price", styles['SectionHeader']),
            Paragraph("Discount (%)", styles['SectionHeader']),
            Paragraph("VAT (%)", styles['SectionHeader']),
            Paragraph("Amount", styles['SectionHeader'])
        ]
    ]

    for item in invoice_data['items']:
        table_data.append([
            Paragraph(item['description'], styles['Normal']),
            Paragraph(str(item['quantity']), styles['Normal']),
            Paragraph(f"{item['unit_price']:.2f} {invoice_data['currency']}", styles['Normal']),
            Paragraph(f"{item['discount']}%", styles['Normal']),
            Paragraph(f"{item['vat_rate']}%", styles['Normal']),
            Paragraph(f"{item['amount']:.2f} {invoice_data['currency']}", styles['Normal'])
        ])

    items_table = Table(table_data, colWidths=[50 * mm, 15 * mm, 25 * mm, 20 * mm, 20 * mm, 30 * mm])
    items_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 3),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 10 * mm))

    # Итоговые суммы
    totals_data = [
        [Paragraph("Subtotal:", styles['Normal']),
         Paragraph(f"{invoice_data['subtotal_excl_vat']:.2f} {invoice_data['currency']}", styles['Normal'])],
        [Paragraph("VAT:", styles['Normal']),
         Paragraph(f"{invoice_data['vat_sum']:.2f} {invoice_data['currency']}", styles['Normal'])],
        [Paragraph("Discount:", styles['Normal']),
         Paragraph(f"-{invoice_data['discount_total']:.2f} {invoice_data['currency']}", styles['Normal'])],
        [Paragraph("<b>Total:</b>", styles['SectionHeader']),
         Paragraph(f"<b>{invoice_data['grand_total']:.2f} {invoice_data['currency']}</b>", styles['SectionHeader'])]
    ]

    totals_table = Table(totals_data, colWidths=[120 * mm, 50 * mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 5 * mm))

    # Сумма прописью
    elements.append(Paragraph(f"<b>Amount in words:</b> {invoice_data['amount_in_words']}", styles['Normal']))
    elements.append(Spacer(1, 15 * mm))

    # Примечания
    if invoice_data['notes']:
        elements.append(Paragraph("<b>Notes:</b>", styles['SectionHeader']))
        elements.append(Paragraph(invoice_data['notes'], styles['Normal']))
        elements.append(Spacer(1, 10 * mm))

    # Подписи
    signature_data = [
        [Paragraph("_________________________", styles['Normal']),
         Paragraph("_________________________", styles['Normal'])],
        [Paragraph(f"Invoiced by: {invoice_data['invoiced_by']}", styles['Normal']),
         Paragraph(f"Invoice received by: {invoice_data['buyer']['name']}", styles['Normal'])],
        [Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']), ""]
    ]

    signature_table = Table(signature_data, colWidths=[90 * mm, 90 * mm])
    elements.append(signature_table)

    doc.build(elements)
    buffer.seek(0)

    # Возвращаем PDF как HTTP-ответ
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{payment.invoice_number}.pdf'
    response.write(buffer.getvalue())
    return response


def profile(request):
    return render(request, template_name='profile.html')
