# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_dashboard, name='client_dashboard'),
    path('api/route/', views.calculate_route, name='calculate_route'),
    path('api/search-location/', views.search_location, name='search_location'),
    path('client/login/', views.client_login_view, name='client_login'),
    path('client/logout/', views.client_logout_view, name='client_logout'),
    path('client/history/', views.client_history, name='client_history'),
    path('client/history/export/', views.export_history_csv, name='export_history_csv'),
    path('client/chat/', views.client_chat, name='client_chat'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/docs/', views.admin_docs, name='admin_docs'),
    path('admin-panel/login/', views.admin_login_view, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-panel/register/', views.admin_register_user, name='admin_register_user'),
    path('admin-panel/routes/', views.admin_routes, name='admin_routes'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('admin-panel/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-panel/nodes/', views.admin_nodes, name='admin_nodes'),
    path('api/admin/modifiers/', views.admin_modifiers_api, name='admin_modifiers_api'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
    path('admin-panel/chat/', views.admin_chat, name='admin_chat_inbox'),
    path('admin-panel/chat/<int:user_id>/', views.admin_chat, name='admin_chat'),
]
