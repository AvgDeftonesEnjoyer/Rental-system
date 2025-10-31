from decimal import Decimal
from unicodedata import decimal
from django.db import models
from django.conf import settings

from rental.models import Rental

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        PROCCESSING = 'processing'
        AUTHORIZED = 'authorized'
        CAPTURED = 'captured'
        FAILED = 'failed'

    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='payment')
    hold_amount = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    #stipe part

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_hold_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_final_intent_id = models.CharField(max_length=255, blank=True, null=True)

    hold_amount_minor = models.BigIntegerField(default=5000)
    final_amount_minor = models.BigIntegerField(default=0)

    status = models.CharField(max_length=15, choices = Status.choices, default = Status.PENDING)

# Create your models here.
