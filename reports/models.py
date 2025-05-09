from django.db import models
from users.models import BasicUser
from missing.models import MissingPerson


class Report(models.Model):
    STATUS_NEW = 'new'
    STATUS_UNVERIFIED = 'unverified'
    STATUS_VERIFIED = 'verified'
    STATUS_FALSE = 'false'

    REPORT_CHOICES = [
        (STATUS_NEW, 'new'),
        (STATUS_VERIFIED, 'verified'),
        (STATUS_FALSE , 'false'),
        (STATUS_UNVERIFIED, 'unverified'),
    ]

    user = models.ForeignKey(BasicUser, on_delete=models.SET_NULL, null=True, blank=True)
    missing_person = models.ForeignKey(MissingPerson, on_delete=models.CASCADE, related_name='reports')
    note = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)
    report_status = models.CharField(max_length=10, choices=REPORT_CHOICES, default=STATUS_NEW)

    def __str__(self) :
        return f"Report by {self.user or 'Anonymous'} about {self.missing_person} on ({self.date_submitted:%Y-%m-%d}) "
     