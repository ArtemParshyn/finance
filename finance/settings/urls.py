from django.urls import path

from settings import views

urlpatterns = [
    path('', views.invoice_settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),
    path('api/update-company-info/', views.ModelViewCompany_User.as_view(), name='update_company_info'),
    path('api/<int:pk>', views.ModelViewCompany_User.as_view(), name='api_settings')
]
