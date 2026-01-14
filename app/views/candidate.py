"""
Class-based views for Candidate model operations
"""
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from app.models import Candidate, Election
from app.forms import CandidateForm


class CandidateCreateView(LoginRequiredMixin, CreateView):
    """Add a candidate to an election"""
    model = Candidate
    form_class = CandidateForm
    template_name = 'app/candidates/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and get election"""
        if not self._is_official(request.user):
            messages.error(request, "You don't have permission to add candidates.")
            return redirect('election_list')
        
        # Get the election for this candidate
        self.election = get_object_or_404(Election, uuid=kwargs['uuid'])
        
        # Check if election can be edited (not active during voting or closed)
        if not self.election.is_editable():
            if self.election.closed_at:
                messages.error(request, "Cannot add candidates to a closed election.")
            else:
                messages.error(request, "Cannot add candidates during active voting period.")
            return redirect('election_detail', uuid=self.election.uuid)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Associate candidate with the election and create profile if needed"""
        form.instance.election = self.election
        response = super().form_valid(form)
        
        # Create user profile if it doesn't exist (since they're now a candidate)
        from app.models import Profile
        Profile.objects.get_or_create(user=self.object.user)
        
        messages.success(
            self.request, 
            f"Candidate '{self.object.user.get_full_name()}' has been added to the election!"
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('election_detail', kwargs={'uuid': self.election.uuid})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['election'] = self.election
        
        # Check if there are any available candidates
        from django.contrib.auth.models import User
        from app.models import Candidate
        
        existing_candidate_users = Candidate.objects.filter(
            election=self.election
        ).values_list('user_id', flat=True)
        
        available_users = User.objects.filter(
            is_active=True,
            groups__name='Candidates'
        ).exclude(id__in=existing_candidate_users).distinct()
        
        context['no_candidates_available'] = available_users.count() == 0
        
        return context
    
    def get_form_kwargs(self):
        """Add election to the form kwargs for validation"""
        kwargs = super().get_form_kwargs()
        kwargs['election'] = self.election
        return kwargs
    
    def _is_official(self, user):
        """Check if user is an official who can manage candidates"""
        return user.is_superuser or user.groups.filter(name='Officials').exists()


class CandidateUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing candidate"""
    model = Candidate
    form_class = CandidateForm
    template_name = 'app/candidates/edit.html'
    
    def get_object(self, queryset=None):
        """Get the candidate object and set the election"""
        obj = super().get_object(queryset)
        self.election = obj.election
        return obj
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and get election"""
        if not self._is_official(request.user):
            messages.error(request, "You don't have permission to edit candidates.")
            return redirect('election_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks"""
        candidate = self.get_object()
        
        # Check if election can be edited (not active during voting or closed)
        if not self.election.is_editable():
            if self.election.closed_at:
                messages.error(request, "Cannot edit candidates in a closed election.")
            else:
                messages.error(request, "Cannot edit candidates during active voting period.")
            return redirect('candidate_detail', uuid=candidate.uuid)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request with permission checks"""
        candidate = self.get_object()
        
        # Check if election can be edited (not active during voting or closed)
        if not self.election.is_editable():
            if self.election.closed_at:
                messages.error(request, "Cannot edit candidates in a closed election.")
            else:
                messages.error(request, "Cannot edit candidates during active voting period.")
            return redirect('candidate_detail', uuid=candidate.uuid)
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Candidate '{self.object.user.get_full_name()}' has been updated successfully!"
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('election_detail', kwargs={'uuid': self.election.uuid})
    
    def get_context_data(self, **kwargs):
        """Add election to context"""
        context = super().get_context_data(**kwargs)
        context['election'] = self.election
        return context
    
    def _is_official(self, user):
        """Check if user is an official who can manage candidates"""
        return user.is_superuser or user.groups.filter(name='Officials').exists()


class CandidateDeleteView(LoginRequiredMixin, DeleteView):
    """Remove a candidate from an election"""
    model = Candidate
    template_name = 'app/candidates/delete.html'
    
    def get_object(self, queryset=None):
        """Get the candidate object and set the election"""
        obj = super().get_object(queryset)
        self.election = obj.election
        return obj
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and election status"""
        # Check if user can remove candidates from this election
        candidate = self.get_object()
        if not self._can_remove_candidate(request.user, self.election):
            messages.error(request, "You don't have permission to remove candidates from this election.")
            return redirect('election_detail', uuid=self.election.uuid)
        
        # Check if election can be edited (not active during voting or closed)
        if not self.election.is_editable():
            if self.election.closed_at:
                messages.error(request, "Cannot remove candidates from a closed election.")
            else:
                messages.error(request, "Cannot remove candidates during active voting period.")
            return redirect('candidate_detail', uuid=candidate.uuid)
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Handle candidate deletion"""
        candidate = self.get_object()
        candidate_name = str(candidate)  # Uses the __str__ method which calls get_full_name()
        
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request, 
            f"Candidate '{candidate_name}' has been removed from the election."
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('election_detail', kwargs={'uuid': self.election.uuid})
    
    def get_context_data(self, **kwargs):
        """Add election to context"""
        context = super().get_context_data(**kwargs)
        context['election'] = self.election
        return context
    
    def _can_remove_candidate(self, user, election):
        """Check if user can remove candidates from this election"""
        # User can remove candidates if they are:
        # 1. The election creator/owner
        # 2. Superuser 
        # 3. Election manager (using new user extension)
        return (user == election.created_by or 
                user.is_superuser or 
                user.is_election_manager())
    
    def _is_official(self, user):
        """Check if user is an official who can manage candidates"""
        return user.is_superuser or user.groups.filter(name='Officials').exists()


class CandidateDetailView(DetailView):
    """View a candidate's profile"""
    model = Candidate
    template_name = 'app/candidates/detail.html'
    context_object_name = 'candidate'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def dispatch(self, request, *args, **kwargs):
        """Verify candidate exists"""
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        candidate = self.get_object()
        election = candidate.election
        context['election'] = election
        
        if self.request.user.is_authenticated:
            # Check if current user has voted in this election
            from app.models import Vote
            user_votes = Vote.objects.filter(election=election, user=self.request.user)
            context['voted'] = user_votes.count()
            
            # Check if current user can remove this candidate
            context['can_remove_candidate'] = self._can_remove_candidate(
                self.request.user, 
                election
            )
        else:
            context['voted'] = 0
            context['can_remove_candidate'] = False
        
        return context
    
    def _can_remove_candidate(self, user, election):
        """Check if user can remove candidates from this election"""
        if not user.is_authenticated:
            return False
        # User can remove candidates if they are:
        # 1. The election creator/owner
        # 2. Superuser 
        # 3. Election manager (using new user extension)
        return (user == election.created_by or 
                user.is_superuser or 
                user.is_election_manager())