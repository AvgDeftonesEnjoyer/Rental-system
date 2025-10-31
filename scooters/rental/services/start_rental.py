from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from rental.models import Scooter, Reservation, Rental, Tariff
from .locks import lock_scope

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
        return rental

    raise ValidationError(f'Scooter {scooter_num} is not available')

@transaction.atomic
def end_rental(scooter_num, user):
    rental = Rental.objects.select_for_update().get(scooter=scooter_num, user=user, status=Rental.Status.ACTIVE)
    rental.end_time = timezone.now()
    rental.status = Rental.Status.COMPLETED
    rental.calculate_total_cost()
    rental.save(update_fields=['end_time', 'status', 'total_minutes', 'total_cost'])

    scooter = Scooter.objects.select_for_update().get(num=scooter_num)
    scooter.status = Scooter.Status.AVAILABLE
    scooter.save(update_fields=['status'])

    return rental

