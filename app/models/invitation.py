"""
Invitation model for managing private election access
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid as uuid_module


class Invitation(models.Model):
    """Model representing an invitation to vote in a private election"""
    
    INVITATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    uuid = models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, db_index=True)
    election = models.ForeignKey(
        'Election', 
        on_delete=models.CASCADE, 
        related_name='invitations'
    )
    invited_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='election_invitations',
        null=True,
        blank=True,
        help_text="User being invited (if they have an account)"
    )
    invited_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address of the person being invited (optional for one-time links)"
    )
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    
    # One-time link support
    is_one_time_link = models.BooleanField(
        default=False,
        help_text="If True, this is a one-time anonymous link that can be used by anyone"
    )
    used_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invitations',
        help_text="User who used this one-time link"
    )
    
    # Invitation details
    invitation_token = models.UUIDField(
        default=uuid_module.uuid4, 
        unique=True, 
        editable=False
    )
    status = models.CharField(
        max_length=20, 
        choices=INVITATION_STATUS_CHOICES, 
        default='pending'
    )
    message = models.TextField(
        blank=True, 
        help_text="Optional personal message with the invitation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        help_text="When this invitation expires"
    )
    
    def __str__(self):
        return f"Invitation to {self.invited_email} for {self.election.name}"
    
    def is_expired(self):
        """Check if this invitation has expired"""
        return timezone.now() > self.expires_at
    
    def can_accept(self):
        """Check if this invitation can be accepted"""
        from django.utils import timezone
        now = timezone.now()
        
        # Users can accept invitations as long as:
        # 1. Invitation is pending
        # 2. Invitation hasn't expired  
        # 3. Election hasn't ended yet (can accept for future elections)
        return (self.status == 'pending' and 
                not self.is_expired() and 
                now <= self.election.end_date)
    
    def accept(self, user=None):
        """Accept the invitation"""
        if not self.can_accept():
            return False
        
        self.status = 'accepted'
        self.responded_at = timezone.now()
        
        # Link to user account if provided
        if user and not self.invited_user:
            self.invited_user = user
        
        self.save()
        return True
    
    def decline(self):
        """Decline the invitation"""
        if self.status != 'pending':
            return False
        
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()
        return True
    
    def mark_as_sent(self):
        """Mark invitation as sent via email"""
        self.sent_at = timezone.now()
        self.save()
    
    def get_invitation_url(self):
        """Get the URL for accepting this invitation"""
        from django.urls import reverse
        return reverse('invitation_accept', kwargs={'token': self.invitation_token})
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['election', 'invited_email']]  # Prevent duplicate invitations
        verbose_name = "Election Invitation"
        verbose_name_plural = "Election Invitations"