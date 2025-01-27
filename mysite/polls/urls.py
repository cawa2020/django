from django.urls import path

from . import views

urlpatterns = [
    path('registration', views.registration, name='registration'),
    path('authorization', views.authorization, name='authorization'),
    path('logout', views.logout, name='logout'),
    path('flight', views.flight, name='flight'),
    path('gagarin-flight', views.gagarin_flight, name='gagarin_flight'),
    
    path('lunar-missions', views.lunar_missions, name='lunar_missions'),
    path('lunar-missions/<str:mission_name>', views.lunar_mission_detail, name='lunar_mission_detail'),
    path('lunar-watermark', views.lunar_watermark, name='lunar_watermark'),
    
    path('space-flights', views.space_flights, name='space_flights'),
    path('book-flight', views.book_flight, name='book_flight'),
    path('search', views.search, name='search'),
]