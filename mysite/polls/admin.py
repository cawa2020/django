from django.contrib import admin
from .models import (
    User, LunarCoordinates, LaunchSite, LandingSite,
    CrewMember, Spacecraft, LunarMission, SpaceFlight,
    FlightBooking, WatermarkedImage
)

admin.site.register(User)
admin.site.register(LunarCoordinates)
admin.site.register(LaunchSite)
admin.site.register(LandingSite)
admin.site.register(CrewMember)
admin.site.register(Spacecraft)
admin.site.register(LunarMission)
admin.site.register(SpaceFlight)
admin.site.register(FlightBooking)
# admin.site.register(FlightBooking)
# admin.site.register(WatermarkedImage)