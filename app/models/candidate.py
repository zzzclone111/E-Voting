"""
Candidate model for managing election candidates
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from .election import Election
from .party import Party


class Candidate(models.Model):
    """Model representing a candidate in an election"""
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    symbol = models.FileField(upload_to='uploads/', null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.PROTECT, null=True, blank=True)
    election = models.ForeignKey(Election, on_delete=models.PROTECT, related_name='candidates')
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def get_display_name(self):
        """Get the candidate's display name with fallback"""
        return self.user.get_full_name() or self.user.username
    
    def get_party_name(self):
        """Get the party name or return 'Independent'"""
        return self.party.name if self.party else 'Independent'
    
    class Meta:
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        ordering = ['election', 'user__last_name', 'user__first_name']
        unique_together = ('user', 'election')  # One candidate per user per election