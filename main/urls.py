# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_dashboard, name='client_dashboard'),
    path('api/route/', views.calculate_route, name='calculate_route'),
    path('api/search-location/', views.search_location, name='search_location'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/login/', views.admin_login_view, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-panel/register/', views.admin_register_user, name='admin_register_user'),
    path('admin-panel/routes/', views.admin_routes, name='admin_routes'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/nodes/', views.admin_nodes, name='admin_nodes'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
]
