from django.db import models
from django.contrib.auth import get_user_model
from missing.models import MissingPerson
from django.utils import timezone

User = get_user_model()

class AIMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    original_case = models.ForeignKey(
        MissingPerson, 
        on_delete=models.CASCADE, 
        related_name='ai_matches_as_original'
    )
    matched_case = models.ForeignKey(
        MissingPerson, 
        on_delete=models.CASCADE, 
        related_name='ai_matches_as_match'
    )
    confidence_score = models.FloatField(
        help_text="Confidence percentage (0-100)"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    #algorithm_used = models.CharField(max_length=100, default='face_recognition')
    face_distance = models.FloatField(null=True, blank=True)
    processing_date = models.DateTimeField(auto_now_add=True)
    
    """
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_ai_matches'
    )
    """
    review_date = models.DateTimeField(null=True, blank=True)
    #admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['original_case', 'matched_case']
        ordering = ['-confidence_score', '-created_at']
        
    def __str__(self):
        return f"Match: {self.original_case.full_name} → {self.matched_case.full_name} ({self.confidence_score}%)"
    
    @property
    def confidence_level(self):
        if self.confidence_score is None:
            return 'unknown'
        if self.confidence_score >= 90:
            return 'high'
        elif self.confidence_score >= 46:
            return 'medium'
        else:
            return 'low'
    
    def confirm_match(self, admin_user, notes=""):
        self.status = 'confirmed'
       # self.reviewed_by = admin_user
        self.review_date = timezone.now()
        #self.admin_notes = notes
        self.save()
        
        self.original_case.status = 'found'
        self.original_case.save()
        
        return self
    
    def reject_match(self, admin_user, notes=""):
        self.status = 'rejected'
       # self.reviewed_by = admin_user
        self.review_date = timezone.now()
       # self.admin_notes = notes
        self.save()
        
        return self