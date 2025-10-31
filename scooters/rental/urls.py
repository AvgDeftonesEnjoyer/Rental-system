from django.urls import path
from rest_framework.routers import DefaultRouter

from rental.views import ScooterViewSet, ReservationViewSet, RentalViewSet, TariffViewSet

router = DefaultRouter()
router.register(r'scooters', ScooterViewSet, basename='scooter')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'rentals', RentalViewSet, basename='rental')
router.register(r'tariffs', TariffViewSet, basename='tariff')

urlpatterns = router.urls