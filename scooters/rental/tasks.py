from django.utils import timezone
from celery import shared_task
from django.db import transaction

from .models import Reservation, Scooter

@shared_task
def expire_reservations():
    now = timezone.now()
    qs = Reservation.objects.select_related('scooter').filte(is_active=True, expires_at__lt=now)
    for res in qs:
        with transaction.atomic():
            sc = Scooter.objects.select_for_update().get(num = res.scooter.num)
            res.is_active = False
            res.save(update_fields=['is_active'])
            if sc.status == Scooter.Status.RESERVED:
                sc.status = Scooter.Status.AVAILABLE
                sc.save(update_fields=['status'])
    return len(qs)
            