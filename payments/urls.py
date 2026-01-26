"""
Payment URL configuration
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment methods
    path('methods/', views.payment_methods_list, name='payment_methods'),
    path('methods/add/', views.add_payment_method, name='add_payment_method'),
    path('methods/<uuid:method_id>/remove/', views.remove_payment_method, name='remove_payment_method'),
    path('methods/<uuid:method_id>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    
    # Payment processing
    path('checkout/', views.checkout, name='checkout'),
    path('create-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('success/<uuid:payment_id>/', views.payment_success, name='success'),
    path('cancel/', views.payment_cancel, name='cancel'),
    
    # Payment history
    path('history/', views.payment_history, name='history'),
    path('<uuid:payment_id>/', views.payment_detail, name='detail'),
    path('<uuid:payment_id>/refund/', views.request_refund, name='request_refund'),
    
    # Webhooks
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
