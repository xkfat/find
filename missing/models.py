
from django.db import models
from users.models import BasicUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import date

GENDER = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]

CASE_STATUS = [
    ('missing', 'Missing'),
    ('found', 'Found'),
    ('under_investigation', 'Investigating'),
]

SUBMISSION_STATUS = [
    ('active', 'Active'),
    ('in_progress', 'In Progress'),
    ('closed', 'Closed'),
    ('rejected', 'Rejected'),
]


class MissingPerson(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    gender = models.CharField(max_length=6, choices=GENDER)
    photo = models.ImageField(upload_to='cases_photos/', null=False, blank=False)
    description = models.TextField(blank=True)
    last_seen_date = models.DateField(null=False, blank=False)
    last_seen_location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    reporter = models.ForeignKey(BasicUser, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=CASE_STATUS, default='missing')  
    date_reported = models.DateTimeField(auto_now_add=True)
    submission_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='in_progress')


    def __str__(self):
        return f"{self.first_name} {self.last_name} "
    

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_missing(self):
        if self.pk is None or not self.last_seen_date:
            return 0
        today = date.today()
        delta = today - self.last_seen_date
        return delta.days
    
    @property
    def current_age(self):
        if self.pk is None or not self.last_seen_date:
            return self.age if self.age else 0
        years_missing = timezone.now().year - self.last_seen_date.year
        if years_missing > 0:
            return self.age + years_missing
        else:
            return self.age
        
class CaseUpdate(models.Model):
    case = models.ForeignKey(MissingPerson, on_delete=models.CASCADE, related_name='updates')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp'] 
    
    def __str__(self):
        return f"Update for {self.case.full_name} on {self.timestamp.strftime('%d/%m/%Y')}"
    
    @property
    def formatted_date(self):
        return self.timestamp.strftime('%d/%m/%Y')