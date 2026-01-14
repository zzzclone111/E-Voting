"""
Vote model for managing votes in elections
"""
import json
import uuid
from hashlib import sha256
from django.db import models
from django.contrib.auth.models import User
from .election import Election
from app.encryption import Encryption


class Vote(models.Model):
    """Model representing a vote cast by a user in an election"""
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.PROTECT, related_name='votes')
    ballot = models.CharField(max_length=5000, default="", editable=False)
    hashed = models.CharField(max_length=128, default="", editable=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.election.name}"
    
    def get_receipt_hash(self):
        """Get a shortened version of the hash for display"""
        return self.hashed[:16] + "..." if self.hashed else "N/A"
    
    def save(self, *args, **kwargs):
        """Override save to handle ballot encryption"""
        if not self.ballot and hasattr(self, '_candidate'):
            try:
                self._encrypt_ballot()
            except Exception as e:
                print(f"Error during vote encryption: {e}")
                raise
        
        super().save(*args, **kwargs)
    
    def _encrypt_ballot(self):
        """Encrypt the ballot using homomorphic encryption"""
        candidates = self.election.candidates.order_by('id')
        candidate_ids = [candidate.id for candidate in candidates]
        
        # Create binary ballot (1 for selected candidate, 0 for others)
        unencrypted_ballot = [1 if x == self._candidate.id else 0 for x in candidate_ids]
        
        # Parse and use public key for encryption
        cleaned_key = self.election.public_key.replace("'", '"')
        public_key = json.loads(cleaned_key)
        encryption = Encryption(public_key=f"{public_key['g']},{public_key['n']}")
        
        # Encrypt each vote in the ballot
        encrypted_ballot = []
        for vote in unencrypted_ballot:
            encrypted_vote = encryption.encrypt(vote)
            encrypted_ballot.append(encrypted_vote.ciphertext)
        
        self.ballot = encrypted_ballot
        print(f"Encrypted ballot: {encrypted_ballot}")
        
        # Create hash for vote receipt
        data_to_hash = str(encrypted_ballot)
        self.hashed = sha256(data_to_hash.encode()).hexdigest()
        print(f"Hashed vote: {self.hashed}")
        
        # Clean up temporary attribute
        delattr(self, '_candidate')
    
    class Meta:
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        unique_together = ('user', 'election')  # One vote per user per election
        ordering = ['-created']