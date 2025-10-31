from django.contrib import admin
from rental.models import Scooter, Reservation, Rental, Tariff

# Register your models here.
admin.site.register(Scooter)
admin.site.register(Reservation)
admin.site.register(Rental)
admin.site.register(Tariff)
