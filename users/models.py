from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
 LANGUAGE_ENGLISH = 'en'
 LANGUAGE_FRENCH = 'fr'
 LANGUAGE_ARABIC = 'ar'

 LANGUAGE_CHOICES = [
    (LANGUAGE_ENGLISH, 'English'),
    (LANGUAGE_FRENCH, 'Français'),
    (LANGUAGE_ARABIC, 'العربية'),
 ]

 THEME_LIGHT = 'light'
 THEME_DARK = 'dark'

 THEME_CHOICES = [
    (THEME_LIGHT, 'Light'),
    (THEME_DARK, 'Dark'),
 ]
 phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
 profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
 language = models.CharField(max_length=10,  choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH)
 theme = models.CharField(max_length=10, choices=THEME_CHOICES, default=THEME_LIGHT)
 location_permission = models.BooleanField(default=False)

def __str__(self):
     return self.username 
