"""
URL configuration for the EYTGaming Store app.
"""

from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Product catalog URLs
    path('', views.product_list, name='product_list'),
    path('products/', views.product_list, name='products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout_initiate, name='checkout_initiate'),
    path('checkout/shipping/', views.checkout_shipping, name='checkout_shipping'),
    path('checkout/payment/', views.checkout_payment, name='checkout_payment'),
    path('checkout/confirm/', views.checkout_confirm, name='checkout_confirm'),
    
    # Stripe payment URLs
    path('payment/stripe/create-intent/', views.stripe_create_payment_intent, name='stripe_create_intent'),
    path('payment/stripe/confirm/', views.stripe_confirm_payment, name='stripe_confirm'),
    path('payment/stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Paystack payment URLs
    path('payment/paystack/initialize/', views.paystack_initialize, name='paystack_initialize'),
    path('payment/paystack/verify/', views.paystack_verify, name='paystack_verify'),
    path('payment/paystack/webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Review URLs
    path('product/<slug:product_slug>/reviews/', views.product_reviews, name='product_reviews'),
    path('product/<slug:product_slug>/review/submit/', views.submit_review, name='submit_review'),
    
    # Newsletter URLs
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    
    # Order URLs will be added in later tasks
]
