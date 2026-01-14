"""
User profile model for extended user information
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Extended user profile information"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile = models.TextField(blank=True, help_text="User's background and qualifications")  
    manifesto = models.TextField(blank=True, help_text="User's policy positions and campaign promises")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, help_text="Profile picture")
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")
    location = models.CharField(max_length=200, blank=True, help_text="City, State/Province, Country")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, help_text="Gender identity")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"
        
    def get_display_name(self):
        """Get the user's display name with fallback"""
        return self.user.get_full_name() or self.user.username
    
    def get_age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def get_gender_display_short(self):
        """Get short gender display"""
        return dict(self.GENDER_CHOICES).get(self.gender, '')
    
    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ['user__last_name', 'user__first_name']