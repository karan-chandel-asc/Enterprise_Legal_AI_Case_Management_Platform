from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('dashboard-api/', views.DashboardApi.as_view(), name='dashboard_api'),
]
