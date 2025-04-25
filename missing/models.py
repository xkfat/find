from django.db import models
from users.models import BasicUser
from django.utils import timezone
from django.core.validators import  MinValueValidator

GENDER = [
    ('M', 'Male'),
    ('F', 'Female'),
]

STATUS = [
    ('searching', 'Searching'),
    ('found', 'found'),
    ('under_investigation', 'under_investigation'),
]


class MissingPerson(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    gender = models.CharField(max_length=1, choices=GENDER)
    photo = models.ImageField(upload_to='cases_photos/', null=False, blank=False)
    description = models.TextField(blank=True)
    last_seen_date = models.DateField()
    last_seen_location = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    reporter = models.ForeignKey(BasicUser, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS, default='searching')
    date_reported = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} "
    
    @property
    def current_age(self):
        years_missing = timezone.now().year - self.last_seen_date.year
        if years_missing > 0:
            return self.age + years_missing
        else:
            return self.age 