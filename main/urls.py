# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/route/', views.calculate_route, name='calculate_route'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/login/', views.admin_login_view, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-panel/register/', views.admin_register_user, name='admin_register_user'),
]
