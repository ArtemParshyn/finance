from django.urls import path
from back import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
