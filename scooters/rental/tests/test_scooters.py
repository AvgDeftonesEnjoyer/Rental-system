from datetime import timedelta
from django.utils import timezone

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User

from rental.models import Scooter, Tariff, Reservation, Rental
from rental.services.reserve import reserve_scooter

class ScooterTestCase(TestCase):
    def setUp(self):
        self.scooter = Scooter.objects.create(num=546, status=Scooter.Status.AVAILABLE)
        self.scooter.full_clean()
        self.scooter.save()

    def test_scooter_creation(self):
        self.assertEqual(self.scooter.num, 546)
        self.assertEqual(self.scooter.status, Scooter.Status.AVAILABLE)
        self.assertEqual(self.scooter.battery_level, 100)
        self.assertIsNotNone(self.scooter.created_at)

    def test_scooter_uniqueness(self):
        with self.assertRaises(IntegrityError):
            Scooter.objects.create(num=546, status=Scooter.Status.AVAILABLE)

    def test_scooter_validation(self):
        self.scooter.battery_level = -1
        with self.assertRaises(ValidationError):
            self.scooter.full_clean()
        self.scooter.battery_level = 101
        with self.assertRaises(ValidationError):
            self.scooter.full_clean()
        self.scooter.battery_level = 50
        self.scooter.full_clean()
        self.assertEqual(self.scooter.battery_level, 50)

    def test_tariff_creation(self):
        tariff = Tariff.objects.create(name='test', per_minute=10.00)
        self.assertEqual(tariff.name, 'test')
        self.assertEqual(tariff.per_minute, 10.00)

class ReservationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testReservationUser1')
        self.scooter = Scooter.objects.create(num=546, status=Scooter.Status.AVAILABLE)

    def test_reservation_creation(self):
        reservation = Reservation.objects.create(scooter=self.scooter, user=self.user)
        self.assertEqual(reservation.scooter, self.scooter)
        self.assertEqual(reservation.user, self.user)
        self.assertTrue((timezone.now() - reservation.start_time).total_seconds() < 2)
        delta = reservation.expires_at - reservation.start_time
        self.assertTrue(abs(delta - timedelta(minutes=5)) < timedelta(seconds=1))
        self.assertTrue(reservation.is_active)

    def test_reservation_uniqueness(self):
        Reservation.objects.create(scooter=self.scooter, user=self.user)
        with self.assertRaises(IntegrityError):
            Reservation.objects.create(scooter=self.scooter, user=self.user)

class RentalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testRentalUser1')
        self.scooter = Scooter.objects.create(num=546, status=Scooter.Status.AVAILABLE)
        self.tariff = Tariff.objects.create(name='test', per_minute=10.00)

    def test_rental_creation(self):
        rental = Rental.objects.create(scooter=self.scooter, user=self.user, tariff=self.tariff, status=Rental.Status.ACTIVE)
        self.assertEqual(rental.scooter, self.scooter)
        self.assertEqual(rental.user, self.user)
        self.assertEqual(rental.tariff, self.tariff)
        self.assertEqual(rental.status, Rental.Status.ACTIVE)
        self.assertEqual(rental.total_minutes, 0)
        self.assertEqual(rental.total_cost, 0)
        self.assertTrue((timezone.now() - rental.start_time).total_seconds() < 2)
        self.assertIsNone(rental.end_time)

    def test_rental_uniqueness(self):
        Rental.objects.create(scooter=self.scooter, user=self.user, tariff=self.tariff, status=Rental.Status.ACTIVE)
        with self.assertRaises(IntegrityError):
            Rental.objects.create(scooter=self.scooter, user=self.user, tariff=self.tariff, status=Rental.Status.ACTIVE)

    def test_rental_total_cost(self):
        rental = Rental.objects.create(scooter=self.scooter, user=self.user, tariff=self.tariff, status=Rental.Status.ACTIVE)
        start = timezone.now()
        rental.start_time = start
        rental.end_time = start + timedelta(minutes=5)
        rental.calculate_total_cost()
        rental.save()
        self.assertEqual(rental.total_minutes, 5)
        self.assertEqual(rental.total_cost, 50.00)

class ReserveTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testReserveUser1')
        self.scooter = Scooter.objects.create(num=546, status=Scooter.Status.AVAILABLE)
    
    def test_reserve_scooter(self):
        reservation = reserve_scooter(self.scooter.num, self.user)
        self.scooter.refresh_from_db()
        self.assertEqual(reservation.scooter, self.scooter)
        self.assertEqual(reservation.user, self.user)
        self.assertTrue(reservation.is_active)
        self.assertEqual(reservation.expires_at - reservation.start_time, timedelta(minutes=5))
        self.assertEqual(self.scooter.status, Scooter.Status.RESERVED)

    def test_reserve_scooter_uniqueness(self):
        reserve_scooter(self.scooter.num, self.user)
        with self.assertRaises(ValueError):
            reserve_scooter(self.scooter.num, self.user)

    def test_reserve_scooter_expiry(self):
        reservation = reserve_scooter(self.scooter.num, self.user)
        reservation.expires_at = timezone.now() - timedelta(minutes=1)
        reservation.save()
        self.assertEqual(self.scooter.status, Scooter.Status.AVAILABLE)
