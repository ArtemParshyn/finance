from django.shortcuts import render
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, User


class LandingView(TemplateView):
    template_name = 'landing.html'


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Создаем пользователя без username (он сгенерируется автоматически)
            user = form.save(commit=False)

            # Генерируем username на основе email
            user.username = user.email.split('@')[0]  # или другой метод

            # Проверяем уникальность username
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
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    print(request.user)
    #if request.user.is_authenticated:
    #    return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            print("Login errors:", form.errors)
            messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


@method_decorator(login_required, name='dispatch')
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        # Здесь будет бизнес-логика для получения данных дашборда
        return context


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Обновление профиля
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.company = request.POST.get('company', '')
        user.position = request.POST.get('position', '')
        user.address = request.POST.get('address', '')
        user.bio = request.POST.get('bio', '')
        user.save()
        print(user)
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})