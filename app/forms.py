from django import forms
from django.contrib.auth.models import User
from app.models import Election, Candidate, Party, Invitation
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['name', 'description', 'start_date', 'end_date', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter election name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter election description'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Election Name',
            'description': 'Description',
            'start_date': 'Start Date & Time',
            'end_date': 'End Date & Time',
            'is_public': 'Public Election',
        }
        help_texts = {
            'is_public': 'Check this to allow any registered user to vote. Uncheck for private elections (invitation only).',
        }

    # Add custom field definitions to handle datetime-local format
    start_date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'step': '60'  # 1 minute steps
        }, format='%Y-%m-%dT%H:%M'),
        help_text='Select both date and time for when voting starts'
    )
    
    end_date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'step': '60'  # 1 minute steps
        }, format='%Y-%m-%dT%H:%M'),
        help_text='Select both date and time for when voting ends'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default values only for new elections (not when editing)
        if not self.instance.pk:
            from django.utils import timezone
            from datetime import datetime, time
            
            now = timezone.now()
            # Default start time: Tomorrow at 9:00 AM
            tomorrow = now.date() + timezone.timedelta(days=1)
            default_start = timezone.make_aware(datetime.combine(tomorrow, time(9, 0)))
            
            # Default end time: Same day at 5:00 PM
            default_end = timezone.make_aware(datetime.combine(tomorrow, time(17, 0)))
            
            # Set initial values for the fields
            self.fields['start_date'].initial = default_start.strftime('%Y-%m-%dT%H:%M')
            self.fields['end_date'].initial = default_end.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")


class ElectionUpdateForm(forms.ModelForm):
    """Form for updating elections - includes active field"""
    class Meta:
        model = Election
        fields = ['name', 'description', 'start_date', 'end_date', 'is_public', 'active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter election name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter election description'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Election Name',
            'description': 'Description',
            'start_date': 'Start Date & Time',
            'end_date': 'End Date & Time',
            'is_public': 'Public Election',
            'active': 'Activate Election',
        }
        help_texts = {
            'is_public': 'Check this to allow any registered user to vote. Uncheck for private elections (invitation only).',
            'active': 'Check this box to make the election visible to voters immediately. Uncheck to keep it as a draft.',
        }

    # Add custom field definitions to handle datetime-local format
    start_date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'step': '60'  # 1 minute steps
        }, format='%Y-%m-%dT%H:%M'),
        help_text='Select both date and time for when voting starts'
    )
    
    end_date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'step': '60'  # 1 minute steps
        }, format='%Y-%m-%dT%H:%M'),
        help_text='Select both date and time for when voting ends'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")


class CandidateFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        
        users = []
        for form in self.forms:
            if form.cleaned_data:
                user = form.cleaned_data.get('user')
                if user:
                    if user in users:
                        raise ValidationError("Each user can only be a candidate once per election.")
                    users.append(user)
        
        if len(users) < 2:
            raise ValidationError("An election must have at least 2 candidates.")

class CandidateForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be set properly in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a candidate",
        help_text="Only users in the 'Candidates' group are shown"
    )
    party = forms.ModelChoiceField(
        queryset=Party.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="No Party (Independent)",
        required=False
    )
    symbol = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload candidate symbol (optional)",
        required=False
    )

    class Meta:
        model = Candidate
        fields = ['user', 'party', 'symbol']

    def __init__(self, *args, **kwargs):
        self.election = kwargs.pop('election', None)
        super().__init__(*args, **kwargs)
        
        # Filter out users who are already candidates in this election
        if self.election:
            # Get users who are already candidates in this election
            existing_candidate_users = Candidate.objects.filter(
                election=self.election
            ).values_list('user_id', flat=True)
            
            # Filter the queryset to exclude existing candidates
            available_users = User.objects.filter(
                is_active=True,
                groups__name='Candidates'
            ).exclude(id__in=existing_candidate_users).distinct()
            
            self.fields['user'].queryset = available_users
            
            if available_users.count() == 0:
                if existing_candidate_users:
                    self.fields['user'].help_text = "⚠️ All available candidates are already assigned to this election."
                else:
                    self.fields['user'].help_text = "⚠️ No candidates available. Create users and add them to 'Candidates' group first."
        else:
            # Fallback for when no election is provided
            candidate_users = User.objects.filter(
                is_active=True,
                groups__name='Candidates'
            ).distinct()
            
            if candidate_users.count() == 0:
                self.fields['user'].help_text = "⚠️ No candidates available. Create users and add them to 'Candidates' group first."

    def clean_user(self):
        """Validate that user is not already a candidate in this election"""
        user = self.cleaned_data.get('user')
        if user and hasattr(self, 'election'):
            # Check if this user is already a candidate in this election
            existing_candidate = Candidate.objects.filter(
                user=user, 
                election=self.election
            ).first()
            
            if existing_candidate:
                raise ValidationError(f"{user.get_full_name()} is already a candidate in this election.")
        
        return user


class InvitationForm(forms.ModelForm):
    """Form for sending invitations to private elections"""
    
    invited_emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter email addresses, one per line'
        }),
        help_text='Enter one email address per line',
        label='Email Addresses'
    )
    
    expires_in_days = forms.IntegerField(
        initial=7,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '30'
        }),
        help_text='Number of days until invitation expires (1-30)',
        label='Expires In (Days)'
    )
    
    class Meta:
        model = Invitation
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional personal message for the invitation'
            }),
        }
        labels = {
            'message': 'Personal Message (Optional)',
        }
    
    def __init__(self, *args, **kwargs):
        self.election = kwargs.pop('election', None)
        super().__init__(*args, **kwargs)
    
    def clean_invited_emails(self):
        """Validate and process email addresses"""
        emails_text = self.cleaned_data.get('invited_emails', '')
        
        # Split by lines and clean up
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        if not emails:
            raise ValidationError("Please enter at least one email address.")
        
        # Validate email formats
        from django.core.validators import validate_email
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email.lower())
            except ValidationError:
                raise ValidationError(f"'{email}' is not a valid email address.")
        
        # Check for duplicates
        if len(valid_emails) != len(set(valid_emails)):
            raise ValidationError("Duplicate email addresses found.")
        
        # Check if any of these users are already invited
        if self.election:
            existing_invitations = Invitation.objects.filter(
                election=self.election,
                invited_email__in=valid_emails
            ).values_list('invited_email', flat=True)
            
            if existing_invitations:
                existing_list = list(existing_invitations)
                raise ValidationError(
                    f"The following email addresses already have invitations: {', '.join(existing_list)}"
                )
        
        return valid_emails
    
    def save_invitations(self, invited_by_user):
        """Create individual invitation objects for each email"""
        if not self.election:
            raise ValueError("Election must be set before saving invitations")
        
        emails = self.cleaned_data['invited_emails']
        expires_in_days = self.cleaned_data['expires_in_days']
        message = self.cleaned_data.get('message', '')
        
        invitations = []
        for email in emails:
            # Check if user exists with this email
            try:
                invited_user = User.objects.get(email=email)
            except User.DoesNotExist:
                invited_user = None
            
            invitation = Invitation.objects.create(
                election=self.election,
                invited_user=invited_user,
                invited_email=email,
                invited_by=invited_by_user,
                message=message,
                expires_at=timezone.now() + timedelta(days=expires_in_days)
            )
            invitations.append(invitation)
        
        return invitations


class InvitationResponseForm(forms.Form):
    """Form for accepting or declining invitations"""
    
    RESPONSE_CHOICES = [
        ('accept', 'Accept Invitation'),
        ('decline', 'Decline Invitation'),
    ]
    
    response = forms.ChoiceField(
        choices=RESPONSE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Your Response'
    )