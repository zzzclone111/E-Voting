"""
Base views for general functionality like homepage and profile
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import Election, Vote, Invitation

def index(request):
    """Homepage view showing election summary and ongoing elections"""
    # Get elections organized by status
    all_elections = Election.objects.all().select_related('created_by')
    
    ongoing_elections = []
    upcoming_elections = []
    recently_closed_elections = []
    
    for election in all_elections:
        status = election.get_status()
        if status == 'open':
            ongoing_elections.append(election)
        elif status in ['scheduled', 'inactive']:
            upcoming_elections.append(election)
        elif status in ['closed', 'expired']:
            recently_closed_elections.append(election)
    
    # Sort ongoing elections by end date (soonest ending first)
    ongoing_elections.sort(key=lambda x: x.end_date)
    
    # Get featured elections (up to 4 most recent ongoing or upcoming)
    featured_elections = ongoing_elections[:4]
    if len(featured_elections) < 4:
        remaining_slots = 4 - len(featured_elections)
        upcoming_elections.sort(key=lambda x: x.start_date)
        featured_elections.extend(upcoming_elections[:remaining_slots])
    
    context = {
        'elections': featured_elections,  # For backward compatibility
        'ongoing_elections': ongoing_elections,
        'upcoming_elections': upcoming_elections[:3],  # Show only next 3 upcoming
        'recently_closed_elections': recently_closed_elections[:3],  # Show only last 3 closed
        'elections_count': {
            'ongoing': len(ongoing_elections),
            'upcoming': len(upcoming_elections),
            'recently_closed': len(recently_closed_elections),
            'total': len(all_elections)
        }
    }
    
    return render(request, 'app/index.html', context)

@login_required
def profile(request):
    """User profile view showing their voting history, created elections, and invitations"""
    votes = Vote.objects.filter(user=request.user).select_related('election')
    
    # Get elections created by this user (if they're an official)
    created_elections = Election.objects.filter(created_by=request.user).order_by('-created')
    
    # Add can_edit attribute to each election using the model method
    for election in created_elections:
        # Use the model's is_editable method
        election.can_edit = election.is_editable()
    
    # Get invitations for this user
    invitations = Invitation.objects.filter(
        invited_email=request.user.email
    ).select_related('election').order_by('-created_at')
    
    # Categorize invitations by status
    pending_invitations = invitations.filter(status='pending')
    accepted_invitations = invitations.filter(status='accepted')
    declined_invitations = invitations.filter(status='declined')
    
    return render(request, 'app/profile.html', {
        'votes': votes,
        'created_elections': created_elections,
        'invitations': invitations,
        'pending_invitations': pending_invitations,
        'accepted_invitations': accepted_invitations,
        'declined_invitations': declined_invitations,
        'invitation_counts': {
            'total': invitations.count(),
            'pending': pending_invitations.count(),
            'accepted': accepted_invitations.count(),
            'declined': declined_invitations.count(),
        }
    })

# Legal pages
def terms(request):
    """Terms of Service page"""
    return render(request, 'app/legal/terms.html')

def privacy(request):
    """Privacy Policy page"""
    return render(request, 'app/legal/privacy.html')

def accessibility(request):
    """Accessibility page"""
    return render(request, 'app/legal/accessibility.html')

def contact(request):
    """Contact Us page"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        # In a full implementation, this would handle the contact form submission
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message. We will get back to you within 24-48 hours.')
        return redirect('contact')
    
    return render(request, 'app/legal/contact.html')

def faqs(request):
    """Frequently Asked Questions page"""
    return render(request, 'app/legal/faqs.html')

def how(request):
    """How It Works page explaining the platform"""
    return render(request, 'app/how.html')