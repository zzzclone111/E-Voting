"""
Base models and mixins for common functionality
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """Abstract base model with active/inactive status"""
    
    active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True