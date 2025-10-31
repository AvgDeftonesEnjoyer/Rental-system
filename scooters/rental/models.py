from datetime import timedelta

from django.db import models
from django.db.models import Q

from django.utils import timezone
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Scooter(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available'
        RENTED = 'rented'
        RESERVED = 'reserved'
        UNAVAILABLE = 'unavailable'
    num = models.IntegerField(primary_key=True, unique=True)
    status = models.CharField(max_length= 15, choices=Status.choices)
    battery_level = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
        )


    created_at = models.DateTimeField(auto_now_add=True)

    indexes = [
        models.Index(fields=['status']),
        models.Index(fields=['created_at']),
        models.Index(fields=['battery_level']),
        models.Index(fields=['created_at', 'status']),
    ]


class Tariff(models.Model):
    name = models.CharField(max_length=100, default = 'default')
    per_minute = models.DecimalField(max_digits=10, decimal_places=2, default=3)

    def __str__(self):
        return f'{self.name} - {self.per_minute}$'


def reservation_default_expiry():
    return timezone.now() + timedelta(minutes=5)

class Reservation(models.Model):
    scooter = models.ForeignKey(Scooter, on_delete = models.CASCADE, related_name =  'reservations')
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'reservations')
    start_time = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default = reservation_default_expiry)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['scooter'],
            condition = Q(is_active = True),
            name = 'uniq_active_reservation_per_scooter'
            ),
            models.UniqueConstraint(fields =['user'],
            condition = Q(is_active=True),
            name = 'uniq_active_reservation_per_user'
            ),
        ]
        
    def __str__(self):
        return f'{self.scooter.num} - {self.user.username} - {self.start_time} - {self.expires_at}'


class Rental(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active'
        COMPLETED = 'completed'
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, related_name='rentals')
    user = models.ForeignKey(User, on_delete= models.CASCADE, related_name='rentals')
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, related_name='rentals')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    total_minutes = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='active'),
                name='uniq_active_rental_per_user'
            ),
            models.UniqueConstraint(
                fields=['scooter'],
                condition=models.Q(status='active'),
                name='uniq_active_rental_per_scooter'
            ),
        ]

    def calculate_total_cost(self):
        if not self.end_time:
            return None

        minutes = max(1, int((self.end_time - self.start_time).total_seconds() // 60))

        self.total_minutes = minutes
        self.total_cost = minutes * self.tariff.per_minute

        return self.total_cost

    def __str__(self):
        return f'{self.scooter.num} - {self.user.username} - {self.start_time} - {self.end_time} - {self.status}'



    

# Create your models here.
