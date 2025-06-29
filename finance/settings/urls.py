from django.urls import path, include
from rest_framework.routers import DefaultRouter
from settings import views

router = DefaultRouter()
router.register(r'numbering-templates', views.NumberingTemplateViewSet, basename='numbering-template')

urlpatterns = [
    path('', views.invoice_settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),
    path('api/update-company-info/', views.ModelViewCompany_User.as_view(), name='update_company_info'),
    path('api/<int:pk>', views.ModelViewCompany_User.as_view(), name='api_settings'),
    path('api/', include(router.urls)),  # Добавить URL для шаблонов
]