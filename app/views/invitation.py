"""
Views for managing election invitations
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.sites.models import Site

from app.models import Election, Invitation
from app.forms import InvitationForm, InvitationResponseForm


@login_required
def send_invitations(request, uuid):
    """Send invitations for a private election"""
    election = get_object_or_404(Election, uuid=uuid)
    
    # Check if user can manage this election
    if not election.can_be_edited_by(request.user):
        return HttpResponseForbidden("You don't have permission to manage this election.")
    
    # Check if election can be edited (not closed or during active voting)
    if not election.is_editable():
        if election.closed_at:
            messages.error(request, "Cannot manage invitations for a closed election.")
        else:
            messages.error(request, "Cannot manage invitations during active voting period.")
        return redirect('election_detail', uuid=election.uuid)
    
    # Only private elections can have invitations
    if election.is_public:
        messages.error(request, "Cannot send invitations for public elections.")
        return redirect('election_detail', uuid=election.uuid)
    
    if request.method == 'POST':
        form = InvitationForm(request.POST, election=election)
        if form.is_valid():
            try:
                invitations = form.save_invitations(request.user)
                
                # Send email notifications
                successful_emails = 0
                for invitation in invitations:
                    if send_invitation_email(invitation):
                        invitation.mark_as_sent()
                        successful_emails += 1
                
                messages.success(
                    request, 
                    f"Successfully sent {successful_emails} invitations out of {len(invitations)} total."
                )
                return redirect('manage_invitations', uuid=election.uuid)
                
            except Exception as e:
                messages.error(request, f"Error creating invitations: {str(e)}")
    else:
        form = InvitationForm(election=election)
    
    context = {
        'election': election,
        'form': form,
        'page_title': f'Send Invitations - {election.name}'
    }
    return render(request, 'app/invitations/send_invitations.html', context)


@login_required
def manage_invitations(request, uuid):
    """Manage invitations for an election"""
    election = get_object_or_404(Election, uuid=uuid)
    
    # Check if user can manage this election
    if not election.can_be_edited_by(request.user):
        return HttpResponseForbidden("You don't have permission to manage this election.")
    
    # Check if election can be edited (not closed or during active voting)
    if not election.is_editable():
        if election.closed_at:
            messages.error(request, "Cannot manage invitations for a closed election.")
        else:
            messages.error(request, "Cannot manage invitations during active voting period.")
        return redirect('election_detail', uuid=election.uuid)
    
    invitations = election.invitations.all().order_by('-created_at')
    
    # Calculate invitation counts
    total_invitations = invitations.count()
    pending_invitations = invitations.filter(status='pending').count()
    accepted_invitations = invitations.filter(status='accepted').count()
    declined_expired_invitations = total_invitations - pending_invitations - accepted_invitations
    
    context = {
        'election': election,
        'invitations': invitations,
        'invitation_counts': {
            'total': total_invitations,
            'pending': pending_invitations,
            'accepted': accepted_invitations,
            'declined_expired': declined_expired_invitations,
        },
        'page_title': f'Manage Invitations - {election.name}'
    }
    return render(request, 'app/invitations/manage_invitations.html', context)


def invitation_accept(request, uuid):
    """Handle invitation acceptance/decline"""
    invitation = get_object_or_404(Invitation, invitation_token=uuid)
    
    # Check if invitation is still valid
    if not invitation.can_accept():
        context = {
            'invitation': invitation,
            'error': 'This invitation has expired or is no longer valid.',
            'page_title': 'Invitation Expired'
        }
        return render(request, 'app/invitations/invitation_expired.html', context)
    
    if request.method == 'POST':
        response = request.POST.get('response')
        
        if response == 'accept':
                # User must be logged in to accept
                if not request.user.is_authenticated:
                    # Store the invitation token in session and redirect to login
                    request.session['invitation_token'] = str(uuid)
                    messages.info(request, 'Please log in to accept the invitation.')
                    return redirect('login')
                
                # Accept the invitation
                if invitation.accept(request.user):
                    messages.success(
                        request, 
                        f'You have successfully accepted the invitation to vote in "{invitation.election.name}".'
                    )
                    return redirect('election_detail', uuid=invitation.election.uuid)
                else:
                    messages.error(request, 'Unable to accept invitation. It may have expired.')
        
        elif response == 'decline':
            # Decline the invitation
            if invitation.decline():
                messages.info(
                    request, 
                    f'You have declined the invitation to vote in "{invitation.election.name}".'
                )
                return redirect('/')
            else:
                messages.error(request, 'Unable to decline invitation.')
    
    context = {
        'invitation': invitation,
        'page_title': f'Invitation to {invitation.election.name}'
    }
    return render(request, 'app/invitations/invitation_response.html', context)


@login_required
def resend_invitation(request, uuid):
    """Resend a specific invitation"""
    invitation = get_object_or_404(Invitation, uuid=uuid)
    
    # Check if user can manage this election
    if not invitation.election.can_be_edited_by(request.user):
        return HttpResponseForbidden("You don't have permission to manage this election.")
    
    if invitation.status != 'pending':
        messages.error(request, "Can only resend pending invitations.")
        return redirect('manage_invitations', uuid=invitation.election.uuid)
    
    if send_invitation_email(invitation):
        invitation.mark_as_sent()
        messages.success(request, f"Invitation resent to {invitation.invited_email}")
    else:
        messages.error(request, f"Failed to resend invitation to {invitation.invited_email}")
    
    return redirect('manage_invitations', uuid=invitation.election.uuid)


@login_required
def cancel_invitation(request, uuid):
    """Cancel a pending invitation"""
    invitation = get_object_or_404(Invitation, uuid=uuid)
    
    # Check if user can manage this election
    if not invitation.election.can_be_edited_by(request.user):
        return HttpResponseForbidden("You don't have permission to manage this election.")
    
    if invitation.status != 'pending':
        messages.error(request, "Can only cancel pending invitations.")
        return redirect('manage_invitations', uuid=invitation.election.uuid)
    
    invitation.delete()
    messages.success(request, f"Invitation to {invitation.invited_email} has been cancelled.")
    
    return redirect('manage_invitations', uuid=invitation.election.uuid)


def send_invitation_email(invitation):
    """Send invitation email to the invited user"""
    try:
        # Build the invitation URL using Django sites framework
        invitation_url = invitation.get_invitation_url()
        current_site = Site.objects.get_current()
        # Use https in production, http for development
        protocol = 'https' if getattr(settings, 'USE_TLS', not settings.DEBUG) else 'http'
        full_url = f"{protocol}://{current_site.domain}{invitation_url}"
        
        # Prepare email context
        context = {
            'invitation': invitation,
            'election': invitation.election,
            'invitation_url': full_url,
            'invited_by': invitation.invited_by,
        }
        
        # Render email templates
        subject = f'Invitation to vote in "{invitation.election.name}"'
        text_content = render_to_string('app/emails/invitation_email.txt', context)
        html_content = render_to_string('app/emails/invitation_email.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.invited_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send invitation email: {e}")
        return False


@login_required
def process_pending_invitation(request):
    """Process invitation after user logs in"""
    invitation_token = request.session.get('invitation_token')
    if not invitation_token:
        return redirect('home')
    
    try:
        invitation = Invitation.objects.get(invitation_token=invitation_token)
        if invitation.can_accept():
            if invitation.accept(request.user):
                messages.success(
                    request, 
                    f'You have successfully accepted the invitation to vote in "{invitation.election.name}".'
                )
                # Clear the session
                del request.session['invitation_token']
                return redirect('election_detail', uuid=invitation.election.uuid)
        
        messages.error(request, 'Invitation is no longer valid.')
        del request.session['invitation_token']
        
    except Invitation.DoesNotExist:
        messages.error(request, 'Invitation not found.')
        del request.session['invitation_token']
    
    return redirect('home')