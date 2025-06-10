from django.db import models
from django.contrib.auth.models import AbstractUser

class BasicUser(AbstractUser):
 ROLE_USER = 'user'
 ROLE_ADMIN = 'admin'
 LANGUAGE_ENGLISH = 'english'
 LANGUAGE_FRENCH = 'french'
 LANGUAGE_ARABIC = 'arabic'
 THEME_LIGHT = 'light'
 THEME_DARK = 'dark'

 ROLE_CHOICES = [
    (ROLE_ADMIN, 'Admin'),
    (ROLE_USER, 'User'),
 ]


 LANGUAGE_CHOICES = [
    (LANGUAGE_ENGLISH, 'English'),
    (LANGUAGE_FRENCH, 'Français'),
    (LANGUAGE_ARABIC, 'العربية'),
 ]


 THEME_CHOICES = [
    (THEME_LIGHT, 'Light'),
    (THEME_DARK, 'Dark'),
 ]

 phone_number = models.CharField(max_length=15, null=True, blank=True)
 profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
 language = models.CharField(max_length=10,  choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH)
 theme = models.CharField(max_length=10, choices=THEME_CHOICES, default=THEME_LIGHT)
 location_permission = models.BooleanField(default=False)
 role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
 fcm = models.TextField(blank=True, null=True, help_text="Firebase Cloud Messaging token")

 
 def __str__(self):
          return f"{self.username} ({self.role})"
 
 
 def save(self, *args, **kwargs):
        self.is_staff = (self.role == self.ROLE_ADMIN)
        super().save(*args, **kwargs)