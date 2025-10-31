from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from rental.models import Scooter, Reservation, Tariff
from .locks import lock_scope

RESERVATION_LIFETIME = timedelta(minutes=5)

@transaction.atomic
def reserve_scooter(scooter_num, user):
    lock_key = f'lock:reserve:user:{user.id}:scooter:{scooter_num}'
    with lock_scope(lock_key, ttl_seconds=5) as ok:
        if not ok:
            raise ValueError('Too many requests')
    scooter = Scooter.objects.select_for_update().get(num=scooter_num)
    if scooter.status != Scooter.Status.AVAILABLE:
        raise ValueError(f'Scooter {scooter_num} is not available')
        
    Reservation.objects.filter(user=user, is_active=True).update(is_active=False)

    now = timezone.now()

    reservation = Reservation.objects.create(
        user=user,
        scooter=scooter,
        expires_at=now + RESERVATION_LIFETIME,
        start_time=now,
        is_active=True,
        )
    scooter.status = Scooter.Status.RESERVED
    scooter.save(update_fields=['status'])
    return reservation
