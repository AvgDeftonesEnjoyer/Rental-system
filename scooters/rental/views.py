from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rental.models import Scooter, Reservation, Rental, Tariff
from rental.serializers import ScooterSerializer, ReservationSerializer, RentalSerializer, TariffSerializer
from rental.services.reserve import reserve_scooter
from rental.services.start_rental import start_rental, end_rental


class ScooterViewSet(viewsets.ModelViewSet):
    queryset = Scooter.objects.all()
    serializer_class = ScooterSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def reserve(self, request, pk=None):
        try:
            reservation = reserve_scooter(pk, request.user)
            return Response(ReservationSerializer(reservation).data, status = status.HTTP_201_CREATED)
        except ValueError as e:
            return Response ({'detail': str(e)}, status = status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        try:
            rental = start_rental(pk, request.user)
            return Response(RentalSerializer(rental).data, status = status.HTTP_201_CREATED)
        except ValueError as e:
            return Response ({'detail': str(e)}, status = status.HTTP_400_BAD_REQUEST)


class ReservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user).exclude(is_active=False)

class RentalViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rental.objects.filter(user=self.request.user).order_by('-start_time')

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        try:
            rental = end_rental(pk, request.user)
            return Response(RentalSerializer(rental).data, status = status.HTTP_200_OK)
        except ValueError as e:
            return Response ({'detail': str(e)}, status = status.HTTP_400_BAD_REQUEST)

class TariffViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = TariffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tariff.objects.all()

    


