from rest_framework import serializers
from rental.models import Scooter, Tariff, Reservation, Rental

class ScooterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scooter
        fields = ['num', 'status', 'battery_level', 'created_at']

class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ['name', 'per_minute']

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['scooter', 'user', 'start_time', 'expires_at', 'is_active']

class RentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ['scooter', 'user', 'tariff', 'start_time', 'end_time', 'status', 'total_minutes', 'total_cost']