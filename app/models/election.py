"""
Election model for managing elections in the voting system
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


class Election(models.Model):
    """Model representing an election with its details and status"""
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField()
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_elections', 
        null=True, 
        blank=True
    )
    
    # Encryption-related fields
    private_key = models.CharField(max_length=500, default="", editable=False)
    public_key = models.CharField(max_length=500, default="", editable=False)
    encrypted_positive_total = models.CharField(max_length=5000, default="", editable=False)
    encrypted_negative_total = models.CharField(max_length=5000, default="", editable=False)
    encrypted_zero_sum = models.CharField(max_length=5000, default="", editable=False)
    zero_randomness = models.CharField(max_length=5000, default="", editable=False)
    decrypted_total = models.CharField(max_length=500, default="", editable=False)
    
    # Privacy and access control
    is_public = models.BooleanField(
        default=False, 
        help_text="If True, any registered user can vote. If False, only invited users can vote."
    )
    
    # Status fields
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    
    # Election lifecycle timestamps
    started_at = models.DateTimeField(null=True, blank=True, help_text="When the election was activated")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the election was closed")

    def __str__(self):
        return self.name
    
    def is_voting_open(self):
        """Check if voting is currently open for this election"""
        from django.utils import timezone
        now = timezone.now()
        # Elections are only open when active = True and today is between start and end
        return self.active and self.start_date <= now <= self.end_date
    
    def is_editable(self):
        """Check if this election can be edited"""
        from django.utils import timezone
        now = timezone.now()
        
        # Election is NOT editable if it has been closed
        if self.closed_at is not None:
            return False
        
        # Election is NOT editable if they are active and today is between start and end
        if self.active and self.started_at < now:
            return False
        
        return True
    
    def can_show_results(self):
        """Check if results can be displayed for this election"""
        from django.utils import timezone
        now = timezone.now()
        
        # Election results are available when:
        # 1. Election has been explicitly closed (closed_at is set), OR
        # 2. Election is inactive and voting period has naturally ended
        return (self.closed_at is not None or 
                (not self.active and now > self.end_date))
    
    def get_status(self):
        """Get the current status of the election"""
        from django.utils import timezone
        now = timezone.now()
        
        # If election has been explicitly closed, always return "closed"
        if self.closed_at is not None:
            return "closed"
        
        if not self.active:
            if now > self.end_date:
                return "closed"  # Election is closed and voting period has ended
            else:
                return "inactive"  # Election is inactive (not yet activated)
        else:
            if now < self.start_date:
                return "scheduled"  # Election is active but voting hasn't started
            elif now > self.end_date:
                return "expired"  # Election is active but voting period has ended (needs to be closed)
            else:
                return "open"  # Election is active and voting is open
    
    def get_status_display(self):
        """Get display-friendly status text with appropriate styling class"""
        status = self.get_status()
        status_map = {
            'open': {'text': 'Ongoing', 'class': 'bg-light text-success'},
            'scheduled': {'text': 'Upcoming', 'class': 'bg-light text-warning'},
            'inactive': {'text': 'Upcoming', 'class': 'bg-light text-warning'},  # Change inactive to Upcoming with light bg and warning text
            'expired': {'text': 'Concluded', 'class': 'bg-light text-danger'},
            'closed': {'text': 'Closed', 'class': 'bg-light text-secondary'}
        }
        return status_map.get(status, {'text': 'Unknown', 'class': 'bg-light text-secondary'})
    
    def get_total_votes(self):
        """Get the total number of votes cast in this election"""
        return self.votes.count()
    
    def get_candidates_count(self):
        """Get the number of candidates in this election"""
        return self.candidates.count()
    
    def can_be_edited_by(self, user):
        """Check if a user can edit this election"""
        return (user.is_superuser or 
                self.created_by == user or 
                user.groups.filter(name='Officials').exists())
    
    def can_be_started(self):
        """Check if this election can be started"""
        # Election can only be started if it's not active and hasn't been started before
        return not self.active and self.started_at is None
    
    def can_be_closed(self):
        """Check if this election can be closed"""
        # Election can only be closed if it's active and hasn't been closed before
        return self.active and self.closed_at is None
    
    def start_election(self):
        """Start the election with timestamp"""
        from django.utils import timezone
        if self.can_be_started():
            self.active = True
            self.started_at = timezone.now()
            return True
        return False
    
    def close_election(self):
        """Close the election with timestamp"""
        from django.utils import timezone
        if self.can_be_closed():
            self.active = False
            self.closed_at = timezone.now()
            return True
        return False
    
    def can_user_vote(self, user):
        """Check if a user is authorized to vote in this election"""
        if not user.is_authenticated:
            return False
        
        if self.is_public:
            # Public election - any authenticated user can vote
            return True
        else:
            # Private election - user must be invited
            return self.invitations.filter(
                invited_user=user,
                status='accepted'
            ).exists() or self.invitations.filter(
                invited_email=user.email,
                status='accepted'
            ).exists()
    
    def get_pending_invitations_count(self):
        """Get count of pending invitations"""
        return self.invitations.filter(status='pending').count()
    
    def get_accepted_invitations_count(self):
        """Get count of accepted invitations"""
        return self.invitations.filter(status='accepted').count()
    
    def get_privacy_display(self):
        """Get display-friendly privacy status"""
        return "Public Election" if self.is_public else "Private Election"
    
    def get_results(self):
        if not self.can_show_results():
            return None

        from collections import defaultdict
        import json
        from app.encryption import Encryption

        votes = self.votes.all()
        candidates = self.candidates.all().order_by('id')

        if not votes.exists() or not candidates.exists():
            return None

        candidate_list = list(candidates)
        vote_counts = defaultdict(int)
        total_valid_votes = 0

        try:
            public_key = json.loads(self.public_key.replace("'", '"'))
            private_key = json.loads(self.private_key.replace("'", '"'))
            encryption = Encryption(
                public_key=f"{public_key['g']},{public_key['n']}",
                private_key=private_key['phi']
            )
        except Exception as e:
            print(f"Error loading keys for decryption: {e}")
            return None

        for vote in votes:
            try:
                if isinstance(vote.ballot, list) or (isinstance(vote.ballot, str) and vote.ballot.startswith('[')):
                    ballot_list = vote.ballot
                    if isinstance(ballot_list, str):
                        ballot_list = json.loads(ballot_list.replace("'", '"'))
                    decrypted = [encryption.decrypt(type('Ciphertext', (), {'ciphertext': int(ct)})()) for ct in ballot_list]
                    if 1 in decrypted:
                        selected_candidate_idx = decrypted.index(1)
                        if selected_candidate_idx < len(candidate_list):
                            vote_counts[candidate_list[selected_candidate_idx].id] += 1
                            total_valid_votes += 1
                elif isinstance(vote.ballot, str) and ':' in vote.ballot:
                    candidate_id_str = vote.ballot.split(':')[0]
                    candidate_id = int(candidate_id_str)
                    vote_counts[candidate_id] += 1
                    total_valid_votes += 1
            except Exception as e:
                print(f"Error decrypting vote: {e}")
                continue

        if total_valid_votes == 0:
            return None

        # Create results with candidate details
        results = []
        for candidate in candidates:
            candidate_votes = vote_counts.get(candidate.id, 0)
            percentage = (candidate_votes / total_valid_votes * 100) if total_valid_votes > 0 else 0
            results.append({
                'candidate': candidate,
                'votes': candidate_votes,
                'percentage': round(percentage, 1),
                'party': candidate.party.name if candidate.party else 'Independent'
            })

        # Sort by vote count (descending)
        results.sort(key=lambda x: x['votes'], reverse=True)

        return {
            'results': results,
            'total_votes': total_valid_votes,
            'candidates_count': len(candidates)
        }
    
    class Meta:
        ordering = ['-created']
        verbose_name = "Election"
        verbose_name_plural = "Elections"