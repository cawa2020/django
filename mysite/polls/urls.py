from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('registration', views.registration, name='registration'),
    path('authorization', views.authorization, name='authorization'),
    path('lunar-missions', views.lunar_missions, name='lunar_missions'),
    path('lunar-missions/<int:mission_id>', views.lunar_mission_detail, name='lunar_mission_detail'),
    path('lunar-watermark', views.lunar_watermark, name='lunar_watermark'),
    path('space-flights', views.space_flights, name='space_flights'),
    path('book-flight', views.book_flight, name='book_flight'),
    path('search', views.search, name='search'),
]