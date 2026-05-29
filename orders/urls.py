from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('order/create/', views.create_order_view, name='create_order'),
    path('order/<int:order_id>/rate/', views.rate_order_view, name='rate_order'),    path('order/<int:order_id>/quick-rate/', views.quick_rate_order_view, name='quick_rate_order'),    path('order/<int:order_id>/cancel/', views.cancel_order_request_view, name='cancel_order'),
    path('api/validate-discount/', views.validate_discount_view, name='validate_discount'),
    path('api/services/', views.services_api_view, name='services_api'),
]

