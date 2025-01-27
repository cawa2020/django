from django.db import models
from datetime import datetime
from typing import List
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import re
from django.contrib.auth.hashers import make_password, check_password


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        
        # Проверяем пароль перед хешированием
        if not User.validate_password(password):
            raise ValueError('Password must contain at least 3 characters, including lowercase, uppercase and digit')
            
        user = self.model(email=email, **extra_fields)
        # Хешируем пароль
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    birth_date = models.DateField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'patronymic', 'birth_date']

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"

    def clean(self):
        # Проверка первой буквы в верхнем регистре
        if not self.first_name[0].isupper():
            raise ValueError('Имя должно начинаться с заглавной буквы')
        if not self.last_name[0].isupper():
            raise ValueError('Фамилия должна начинаться с заглавной буквы')
        if not self.patronymic[0].isupper():
            raise ValueError('Отчество должно начинаться с заглавной буквы')

    def set_password(self, raw_password):
        """
        Переопределяем метод установки пароля для добавления валидации
        """
        if raw_password is None:
            self.set_unusable_password()
        else:
            if not self.validate_password(raw_password):
                raise ValueError('Password must contain at least 3 characters, including lowercase, uppercase and digit')
            self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Проверяет соответствие переданного пароля хешу
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
            
        return check_password(raw_password, self.password, setter)

    @staticmethod
    def validate_password(password):
        """
        Валидация пароля
        """
        if not password:
            return False
        if len(password) < 3:
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True


class LunarCoordinates(models.Model):
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"


class LaunchSite(models.Model):
    name = models.CharField(max_length=200)
    location = models.OneToOneField(LunarCoordinates, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class LandingSite(models.Model):
    name = models.CharField(max_length=200)
    coordinates = models.OneToOneField(LunarCoordinates, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CrewMember(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.role}"


class Spacecraft(models.Model):
    command_module = models.CharField(max_length=200)
    lunar_module = models.CharField(max_length=200)
    crew = models.ManyToManyField(CrewMember)

    def __str__(self):
        return f"{self.command_module} / {self.lunar_module}"


class LunarMission(models.Model):
    name = models.CharField(max_length=200)
    spacecraft = models.OneToOneField(Spacecraft, on_delete=models.CASCADE)
    launch_date = models.DateTimeField()
    launch_site = models.ForeignKey(LaunchSite, on_delete=models.CASCADE)
    landing_date = models.DateTimeField()
    landing_site = models.ForeignKey(LandingSite, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class SpaceFlight(models.Model):
    flight_number = models.CharField(max_length=50, unique=True)
    destination = models.CharField(max_length=100)
    launch_date = models.DateTimeField()
    seats_available = models.IntegerField()

    def __str__(self):
        return f"{self.flight_number} to {self.destination}"


class FlightBooking(models.Model):
    flight = models.ForeignKey(SpaceFlight, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('flight', 'user')

    def __str__(self):
        return f"{self.user.full_name} - {self.flight.flight_number}"


class WatermarkedImage(models.Model):
    image = models.ImageField(upload_to='lunar_watermarks/')
    message = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def clean(self):
        if len(self.message) < 10 or len(self.message) > 20:
            raise ValueError('Сообщение должно быть от 10 до 20 символов')

    def __str__(self):
        return f"Watermark: {self.message}"