from django.urls import path

from billing.webhook import stripe_webhook

urlpatterns = [
    path('webhook/', stripe_webhook, name='stripe_webhook'),
]

