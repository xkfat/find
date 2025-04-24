from django.db import models
from users.models import BasicUser
from django.utils import timezone


class Notification(models.Model):
    user = models.ForeignKey(BasicUser, on_delete=models.CASCADE, related_name='notification')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"Sent to {self.user.username}"
    