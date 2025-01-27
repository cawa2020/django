from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import (
    User, LunarMission, LaunchSite, LandingSite, Spacecraft, 
    CrewMember, LunarCoordinates, SpaceFlight, FlightBooking,
    WatermarkedImage
)
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@api_view(['POST'])
@permission_classes([AllowAny])
def registration(request):
    data = request.data
    
    # Валидация данных
    errors = {}
    
    required_fields = ['first_name', 'last_name', 'patronymic', 'email', 'password', 'birth_date']
    for field in required_fields:
        if not data.get(field):
            errors[field] = [f"field {field} can not be blank"]
    
    if errors:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": errors
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # Проверка формата email
    if User.objects.filter(email=data['email']).exists():
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "email": ["Email already exists"]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # Валидация пароля
    if not User.validate_password(data['password']):
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "password": ["Password must contain at least 3 characters, including lowercase, uppercase and digit"]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    try:
        # Создание пользователя
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            patronymic=data['patronymic'],
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        )
        
        # Проверка первых букв
        user.clean()
        
        return Response({
            "data": {
                "user": {
                    "name": user.full_name,
                    "email": user.email
                },
                "code": 201,
                "message": "Пользователь создан"
            }
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "name": [str(e)]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['POST'])
@permission_classes([AllowAny])
def authorization(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "email": ["Email is required"] if not email else [],
                    "password": ["Password is required"] if not password else []
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    user = authenticate(email=email, password=password)
    
    if user is None:
        return Response({
            "message": "Login failed"
        }, status=status.HTTP_403_FORBIDDEN)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
        "data": {
            "user": {
                "id": user.id,
                "name": user.full_name,
                "birth_date": user.birth_date.strftime('%Y-%m-%d'),
                "email": user.email
            },
            "token": str(refresh.access_token)
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lunar_missions(request):
    if request.method == 'GET':
        missions = LunarMission.objects.all()
        data = []
        for mission in missions:
            mission_data = {
                "mission": {
                    "name": mission.name,
                    "launch_details": {
                        "launch_date": mission.launch_details.launch_date.strftime("%Y-%m-%d"),
                        "launch_site": {
                            "name": mission.launch_details.launch_site.name,
                            "location": {
                                "latitude": str(mission.launch_details.launch_site.location.latitude),
                                "longitude": str(mission.launch_details.launch_site.location.longitude)
                            }
                        }
                    },
                    "landing_details": {
                        "landing_date": mission.landing_details.landing_date.strftime("%Y-%m-%d"),
                        "landing_site": {
                            "name": mission.landing_details.landing_site.name,
                            "coordinates": {
                                "latitude": str(mission.landing_details.landing_site.coordinates.latitude),
                                "longitude": str(mission.landing_details.landing_site.coordinates.longitude)
                            }
                        }
                    },
                    "spacecraft": {
                        "command_module": mission.spacecraft.command_module,
                        "lunar_module": mission.spacecraft.lunar_module,
                        "crew": [
                            {
                                "name": member.name,
                                "role": member.role
                            } for member in mission.spacecraft.crew.all()
                        ]
                    }
                }
            }
            data.append(mission_data)
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        try:
            data = request.data['mission']
            
            # Создаем или получаем координаты места запуска
            launch_coords = LunarCoordinates.objects.create(
                latitude=data['launch_details']['launch_site']['location']['latitude'],
                longitude=data['launch_details']['launch_site']['location']['longitude']
            )
            
            # Создаем или получаем место запуска
            launch_site = LaunchSite.objects.create(
                name=data['launch_details']['launch_site']['name'],
                location=launch_coords
            )
            
            # Создаем или получаем координаты места посадки
            landing_coords = LunarCoordinates.objects.create(
                latitude=data['landing_details']['landing_site']['coordinates']['latitude'],
                longitude=data['landing_details']['landing_site']['coordinates']['longitude']
            )
            
            # Создаем или получаем место посадки
            landing_site = LandingSite.objects.create(
                name=data['landing_details']['landing_site']['name'],
                coordinates=landing_coords
            )
            
            # Создаем космический корабль
            spacecraft = Spacecraft.objects.create(
                command_module=data['spacecraft']['command_module'],
                lunar_module=data['spacecraft']['lunar_module']
            )
            
            # Создаем членов экипажа
            for crew_data in data['spacecraft']['crew']:
                crew_member = CrewMember.objects.create(
                    name=crew_data['name'],
                    role=crew_data['role']
                )
                spacecraft.crew.add(crew_member)
            
            # Создаем миссию
            mission = LunarMission.objects.create(
                name=data['name'],
                spacecraft=spacecraft
            )
            
            # Создаем детали запуска
            LunarMission.LaunchDetails.objects.create(
                launch_date=datetime.strptime(data['launch_details']['launch_date'], '%Y-%m-%d'),
                launch_site=launch_site,
                mission=mission
            )
            
            # Создаем детали посадки
            LunarMission.LandingDetails.objects.create(
                landing_date=datetime.strptime(data['landing_details']['landing_date'], '%Y-%m-%d'),
                landing_site=landing_site,
                mission=mission
            )
            
            return Response({
                "data": {
                    "code": 201,
                    "message": "Миссия добавлена"
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "mission": [str(e)]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def lunar_mission_detail(request, mission_id):
    try:
        mission = get_object_or_404(LunarMission, id=mission_id)
        
        if request.method == 'DELETE':
            mission.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        elif request.method == 'PATCH':
            data = request.data['mission']
            
            # Обновляем координаты места запуска
            mission.launch_details.launch_site.location.latitude = data['launch_details']['launch_site']['location']['latitude']
            mission.launch_details.launch_site.location.longitude = data['launch_details']['launch_site']['location']['longitude']
            mission.launch_details.launch_site.location.save()
            
            # Обновляем место запуска
            mission.launch_details.launch_site.name = data['launch_details']['launch_site']['name']
            mission.launch_details.launch_site.save()
            
            # Обновляем координаты места посадки
            mission.landing_details.landing_site.coordinates.latitude = data['landing_details']['landing_site']['coordinates']['latitude']
            mission.landing_details.landing_site.coordinates.longitude = data['landing_details']['landing_site']['coordinates']['longitude']
            mission.landing_details.landing_site.coordinates.save()
            
            # Обновляем место посадки
            mission.landing_details.landing_site.name = data['landing_details']['landing_site']['name']
            mission.landing_details.landing_site.save()
            
            # Обновляем даты
            mission.launch_details.launch_date = datetime.strptime(data['launch_details']['launch_date'], '%Y-%m-%d')
            mission.launch_details.save()
            mission.landing_details.landing_date = datetime.strptime(data['landing_details']['landing_date'], '%Y-%m-%d')
            mission.landing_details.save()
            
            # Обновляем космический корабль
            mission.spacecraft.command_module = data['spacecraft']['command_module']
            mission.spacecraft.lunar_module = data['spacecraft']['lunar_module']
            mission.spacecraft.save()
            
            # Обновляем экипаж
            mission.spacecraft.crew.all().delete()
            for crew_data in data['spacecraft']['crew']:
                crew_member = CrewMember.objects.create(
                    name=crew_data['name'],
                    role=crew_data['role']
                )
                mission.spacecraft.crew.add(crew_member)
            
            # Обновляем название миссии
            mission.name = data['name']
            mission.save()
            
            return Response({
                "data": {
                    "code": 200,
                    "message": "Миссия обновлена"
                }
            }, status=status.HTTP_200_OK)
            
    except LunarMission.DoesNotExist:
        return Response({
            "message": "Not found",
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "mission": [str(e)]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def lunar_watermark(request):
    try:
        if 'fileimage' not in request.FILES:
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "fileimage": ["field fileimage can not be blank"]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        message = request.data.get('message', '')
        if len(message) < 10 or len(message) > 20:
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "message": ["Message must be between 10 and 20 characters"]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        image = Image.open(request.FILES['fileimage'])
        draw = ImageDraw.Draw(image)
        # Здесь должна быть логика добавления водяного знака
        # Для примера просто добавим текст
        draw.text((10, 10), message, fill='white')
        
        # Сохраняем изображение
        watermark = WatermarkedImage.objects.create(
            image=request.FILES['fileimage'],
            message=message,
            user=request.user
        )
        
        # Возвращаем изображение
        response = HttpResponse(content_type='image/jpeg')
        image.save(response, 'JPEG')
        return response
        
    except Exception as e:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "image": [str(e)]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def space_flights(request):
    if request.method == 'GET':
        flights = SpaceFlight.objects.all()
        data = {
            "data": [
                {
                    "flight_number": flight.flight_number,
                    "destination": flight.destination,
                    "launch_date": flight.launch_date.strftime("%Y-%m-%d"),
                    "seats_available": flight.seats_available
                } for flight in flights
            ]
        }
        return Response(data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        try:
            flight = SpaceFlight.objects.create(
                flight_number=request.data['flight_number'],
                destination=request.data['destination'],
                launch_date=datetime.strptime(request.data['launch_date'], '%Y-%m-%d'),
                seats_available=request.data['seats_available']
            )
            return Response({
                "data": {
                    "code": 201,
                    "message": "Космический полет создан"
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "flight": [str(e)]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_flight(request):
    try:
        flight = get_object_or_404(SpaceFlight, flight_number=request.data['flight_number'])
        
        if flight.seats_available <= 0:
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "flight": ["No seats available"]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        # Проверяем, не бронировал ли пользователь этот рейс ранее
        if FlightBooking.objects.filter(flight=flight, user=request.user).exists():
            return Response({
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "errors": {
                        "flight": ["You have already booked this flight"]
                    }
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        # Создаем бронирование
        FlightBooking.objects.create(
            flight=flight,
            user=request.user
        )
        
        # Уменьшаем количество доступных мест
        flight.seats_available -= 1
        flight.save()
        
        return Response({
            "data": {
                "code": 201,
                "message": "Рейс забронирован"
            }
        }, status=status.HTTP_201_CREATED)
        
    except SpaceFlight.DoesNotExist:
        return Response({
            "message": "Not found",
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": {
                "code": 422,
                "message": "Validation error",
                "errors": {
                    "flight": [str(e)]
                }
            }
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
    query = request.GET.get('query', '')
    if not query:
        return Response({
            "data": []
        }, status=status.HTTP_200_OK)
        
    missions = LunarMission.objects.filter(name__icontains=query)
    data = []
    
    for mission in missions:
        mission_data = {
            "type": "Миссия",
            "name": mission.name,
            "launch_date": mission.launch_details.launch_date.strftime("%Y-%m-%d"),
            "landing_date": mission.landing_details.landing_date.strftime("%Y-%m-%d"),
            "crew": [
                {
                    "name": member.name,
                    "role": member.role
                } for member in mission.spacecraft.crew.all()
            ],
            "landing_site": mission.landing_details.landing_site.name
        }
        data.append(mission_data)
        
    return Response({
        "data": data
    }, status=status.HTTP_200_OK)
