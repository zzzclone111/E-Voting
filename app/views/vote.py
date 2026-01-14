"""
Class-based views for voting and result operations
"""
import json
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

from app.models import Election, Candidate, Vote
from app.encryption import Encryption
from app.email_utils import send_vote_confirmation


class VoteView(LoginRequiredMixin, View):
    """Handle user voting for a candidate"""
    
    def get(self, request, uuid):
        """Display voting confirmation page"""
        try:
            candidate = get_object_or_404(Candidate, uuid=uuid)
            election = candidate.election
            
            # Verify candidate belongs to this election
            if candidate.election != election:
                messages.error(request, "Invalid candidate for this election.")
                return redirect('election_detail', uuid=election.uuid)
            
            # Check if voting is allowed
            if not election.is_voting_open():
                messages.error(request, "Voting is not currently open for this election.")
                return redirect('candidate_detail', uuid=candidate.uuid)
            
            # Check if user is authorized to vote
            if not election.can_user_vote(request.user):
                if election.is_public:
                    messages.error(request, "You are not authorized to vote in this election.")
                else:
                    messages.error(request, "This is a private election. You need an invitation to vote.")
                return redirect('candidate_detail', uuid=candidate.uuid)
            
            # Check if user already voted
            if Vote.objects.filter(user=request.user, election=election).exists():
                messages.error(request, "You have already voted in this election.")
                return redirect('candidate_detail', uuid=candidate.uuid)
            
            # Render voting confirmation page
            return render(request, 'app/voting/confirm.html', {
                'election': election,
                'candidate': candidate
            })
            
        except (Election.DoesNotExist, Candidate.DoesNotExist):
            messages.error(request, "Invalid election or candidate.")
            return redirect('election_list')
    
    def post(self, request, uuid):
        """Process a vote submission"""
        try:
            candidate = get_object_or_404(Candidate, uuid=uuid)
            election = candidate.election
            
            # Verify candidate belongs to this election
            if candidate.election != election:
                messages.error(request, "Invalid candidate for this election.")
                return redirect('election_detail', uuid=election.uuid)
            
            # Validate voting conditions
            if not self._can_vote(request.user, election, candidate):
                return redirect('election_detail', uuid=election.uuid)
            
            # Create the vote with proper encryption
            vote = Vote(
                user=request.user, 
                election=election
            )
            vote._candidate = candidate  # Temporary attribute for encryption
            vote.save()  # This will trigger the encryption in the model
            
            # Send confirmation email
            if request.user.email:
                send_vote_confirmation(request.user, election)
            
            messages.success(request, "Your vote has been recorded successfully!")
            return redirect('election_detail', uuid=election.uuid)
            
        except (Election.DoesNotExist, Candidate.DoesNotExist):
            messages.error(request, "Invalid election or candidate.")
            return redirect('election_list')
        except Exception as e:
            messages.error(request, "An error occurred while processing your vote.")
            return redirect('election_list')
    
    def _can_vote(self, user, election, candidate):
        """Check if user can vote in this election for this candidate"""
        # Check if voting is open
        if not election.is_voting_open():
            messages.error(user, "Voting is not currently open for this election.")
            return False
        
        # Check if user is authorized to vote (public election or invited to private election)
        if not election.can_user_vote(user):
            if election.is_public:
                messages.error(user, "You are not authorized to vote in this election.")
            else:
                messages.error(user, "This is a private election. You need an invitation to vote.")
            return False
        
        # Check if user already voted
        if Vote.objects.filter(user=user, election=election).exists():
            messages.error(user, "You have already voted in this election.")
            return False
        
        # Check if candidate belongs to this election
        if candidate.election != election:
            messages.error(user, "Invalid candidate for this election.")
            return False
        
        return True


class CloseElectionView(LoginRequiredMixin, View):
    """Close an election (only for officials)"""
    
    def post(self, request, uuid):
        """Close the specified election"""
        if not request.user.can_close_elections():
            messages.error(request, "You don't have permission to close elections.")
            return redirect('election_detail', uuid=uuid)
        
        try:
            election = get_object_or_404(Election, uuid=uuid)
            
            # Check if election can be closed using the model method
            if not election.can_be_closed():
                if not election.active:
                    messages.warning(request, f"Election '{election.name}' is not currently active.")
                elif election.closed_at:
                    messages.error(request, f"Election '{election.name}' has already been closed.")
                else:
                    messages.error(request, f"Election '{election.name}' cannot be closed at this time.")
                return redirect('election_detail', uuid=uuid)
            
            # Close the election using the model method
            if election.close_election():
                election.save()
                messages.success(request, f"Election '{election.name}' has been closed successfully.")
            else:
                messages.error(request, f"Failed to close election '{election.name}'.")
            
            return redirect('election_detail', uuid=uuid)
            
        except Election.DoesNotExist:
            messages.error(request, "Election not found.")
            return redirect('election_list')


class StartElectionView(LoginRequiredMixin, View):
    """Start/activate an election (only for officials)"""
    
    def post(self, request, uuid):
        """Start the specified election"""
        if not request.user.can_close_elections():  # Using same permission for start/close
            messages.error(request, "You don't have permission to start elections.")
            return redirect('election_detail', uuid=uuid)
        
        try:
            election = get_object_or_404(Election, uuid=uuid)
            
            # Check if election can be started using the model method
            if not election.can_be_started():
                if election.active:
                    messages.warning(request, f"Election '{election.name}' is already active.")
                elif election.started_at:
                    messages.error(request, f"Election '{election.name}' has already been started before and cannot be restarted.")
                else:
                    messages.error(request, f"Election '{election.name}' cannot be started at this time.")
                return redirect('election_detail', uuid=uuid)
            
            # Start the election using the model method
            if election.start_election():
                election.save()
                messages.success(request, f"Election '{election.name}' has been started successfully!")
            else:
                messages.error(request, f"Failed to start election '{election.name}'.")
            
            return redirect('election_detail', uuid=uuid)
            
        except Election.DoesNotExist:
            messages.error(request, "Election not found.")
            return redirect('election_list')


class VerifyResultsView(View):
    """Verify election results using homomorphic encryption"""
    
    def get(self, request, uuid):
        """Display results verification page"""
        try:
            election = get_object_or_404(Election, uuid=uuid)
            
            # Perform verification if election has encryption data
            verified = self._verify_results(election)
            
            return render(request, 'app/elections/verify_results.html', {
                'election': election, 
                'verified': verified
            })
            
        except Election.DoesNotExist:
            raise Http404("Election not found")
    
    def _verify_results(self, election):
        """Verify election results using homomorphic encryption"""
        try:
            if not election.public_key:
                return None  # No encryption data available
            
            # Parse public key
            cleaned_key = election.public_key.replace("'", '"')
            public_key = json.loads(cleaned_key)
            encryption = Encryption(public_key=f"{public_key['g']},{public_key['n']}")
            
            # Convert decrypted total to negative vector
            decrypted_total = json.loads(election.decrypted_total)
            decrypted_negative_total = [-x for x in decrypted_total]
            
            # Encrypt negative total
            encrypted_negative_total = []
            for i in decrypted_negative_total:
                encrypted_negative_total.append(encryption.encrypt(plaintext=i, rand=1))
            
            # Get encrypted positive total and compute zero sum
            encrypted_positive_total = json.loads(election.encrypted_positive_total)
            encrypted_zero_sum = []
            
            for i in range(len(encrypted_positive_total)):
                from app.encryption import Ciphertext
                temp_ept = Ciphertext.from_json(encrypted_positive_total[i])
                encrypted_zero_sum.append(encryption.add(temp_ept, encrypted_negative_total[i]))
            
            # Recalculate zero sum with stored randomness
            zero_randomness = json.loads(election.zero_randomness)
            recalculated_zero_sum = []
            for i in range(len(zero_randomness)):
                recalculated_zero_sum.append(encryption.encrypt(plaintext=0, rand=zero_randomness[i]))
            
            # Verify if sums match
            for i in range(len(encrypted_zero_sum)):
                if encrypted_zero_sum[i].ciphertext != recalculated_zero_sum[i].ciphertext:
                    return False
            
            return True
            
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            # Return None if verification cannot be performed
            return None