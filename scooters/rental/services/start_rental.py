from decimal import Decimal
import uuid
    
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from rental.models import Scooter, Reservation, Rental, Tariff
from .locks import lock_scope
from billing.models import Payment
from billing.services.stripe_service import ensure_customer, create_hold_intent, charge_final_amount, cancel_hold_intent

@transaction.atomic
def start_rental(scooter_num, user):

    lock_key = f'lock:start_rental:user:{user.id}:scooter:{scooter_num}'
    with lock_scope(lock_key, ttl_seconds=5) as ok:
        if not ok:
            raise ValueError('Too many requests')

    now = timezone.now()

    scooter = Scooter.objects.select_for_update().get(num=scooter_num)
    if scooter.status in (Scooter.Status.RESERVED, Scooter.Status.AVAILABLE):
        reservation = None
        if scooter.status == Scooter.Status.RESERVED:
            reservation = (
                Reservation.objects.select_for_update()
                .filter(scooter=scooter, is_active=True)
                .first()
            )
            if reservation is None:
                raise ValidationError(f'Scooter {scooter_num} is reserved but no active reservation found')
            if reservation.user != user:
                raise ValidationError(f'Scooter {scooter_num} is reserved by another user')

        tariff = Tariff.objects.first()
        if tariff is None:
            raise ValidationError('No tariff configured')

        scooter.status = Scooter.Status.RENTED
        scooter.save(update_fields=['status'])
        if reservation is not None:
            reservation.is_active = False
            reservation.save(update_fields=['is_active'])

        rental = Rental.objects.create(
            scooter=scooter,
            user=user,
            tariff=tariff,
            start_time=now,
            status=Rental.Status.ACTIVE,
            total_minutes=0,
            total_cost=0,
        )
        # Create payment with hold amount
        hold_amount = Decimal(str(settings.RENTAL_HOLD_AMOUNT))
        hold_amount_minor = int(hold_amount * 100)
        
        payment = Payment.objects.create(
            rental=rental,
            hold_amount=hold_amount,
            hold_amount_minor=hold_amount_minor,
        )

        customer_id = ensure_customer(user)
        payment.stripe_customer_id = customer_id
        
        hold_intent = create_hold_intent(customer_id, hold_amount_minor)
        payment.stripe_hold_intent_id = hold_intent['id']
        payment.status = Payment.Status.PENDING
        payment.save(update_fields=['stripe_customer_id', 'stripe_hold_intent_id', 'status'])
        
        
        
        return rental

    raise ValidationError(f'Scooter {scooter_num} is not available')

@transaction.atomic
def end_rental(scooter_num, user):
    """End rental and charge final amount."""
    rental = Rental.objects.select_for_update().get(
        scooter__num=scooter_num, 
        user=user, 
        status=Rental.Status.ACTIVE
    )
    
    rental.end_time = timezone.now()
    rental.status = Rental.Status.COMPLETED
    rental.calculate_total_cost()
    rental.save(update_fields=['end_time', 'status', 'total_minutes', 'total_cost'])
    
    payment = Payment.objects.select_for_update().get(rental=rental)
    
    # Calculate final amount in minor currency units (cents)
    final_amount = rental.total_cost
    final_amount_minor = int(final_amount * 100)
    
    # Cancel hold intent if exists
    if payment.stripe_hold_intent_id:
        try:
            cancel_hold_intent(payment.stripe_hold_intent_id)
        except Exception as e:
            # Log error but continue with final charge
            pass

    # Check if payment method is available
    pm_id = payment.stripe_payment_method_id
    if not pm_id:
        raise ValidationError('No payment method found. Hold payment may not have been confirmed.')
    
    # Charge final amount
    idempotency_key = f"final-charge-rental-{rental.id}-{uuid.uuid4()}"
    final_intent = charge_final_amount(
        payment.stripe_customer_id, 
        pm_id, 
        final_amount_minor, 
        settings.RENTAL_CURRENCY, 
        idempotency_key
    )
    
    # Update payment with final charge details
    payment.final_amount = final_amount
    payment.final_amount_minor = final_amount_minor
    payment.stripe_final_intent_id = final_intent["id"]
    payment.status = Payment.Status.PROCCESSING  # Will be updated to CAPTURED by webhook
    payment.save(update_fields=[
        "final_amount", 
        "final_amount_minor", 
        "stripe_final_intent_id", 
        "status"
    ])

    # Update scooter status
    scooter = Scooter.objects.select_for_update().get(num=scooter_num)
    scooter.status = Scooter.Status.AVAILABLE
    scooter.save(update_fields=['status'])

    return rental

