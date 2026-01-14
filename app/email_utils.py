"""
Email utilities for the Intikhab election system.
Provides functions for sending various types of emails using SendGrid.
"""

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """
    Send a welcome email to a newly registered user.
    
    Args:
        user: Django User object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Welcome to Intikhab - Electronic Voting System'
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        Welcome to Intikhab, Pakistan's secure electronic voting platform!
        
        Your account has been successfully created and you're now part of the Citizens group.
        You can now participate in active elections and make your voice heard.
        
        Key features:
        - Secure and transparent voting
        - Real-time election results
        - Easy-to-use interface
        - OAuth integration for quick access
        
        Visit our platform at: http://localhost:8000
        
        Thank you for being part of Pakistan's democratic future!
        
        Best regards,
        The Intikhab Team
        Code for Pakistan
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_election_notification(user, election):
    """
    Send notification about a new election to a user.
    
    Args:
        user: Django User object
        election: Election object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'New Election: {election.name}'
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        A new election has been announced: {election.name}
        
        Election Details:
        - Name: {election.name}
        - Description: {election.description}
        - Voting Period: {election.start_date.strftime('%B %d, %Y at %I:%M %p')} to {election.end_date.strftime('%B %d, %Y at %I:%M %p')}
        
        Make sure to cast your vote during the voting period!
        
        Visit: http://localhost:8000/elections/{election.id}/
        
        Best regards,
        The Intikhab Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Election notification sent to {user.email} for election {election.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send election notification to {user.email}: {str(e)}")
        return False


def send_vote_confirmation(user, election):
    """
    Send vote confirmation email to user.
    
    Args:
        user: Django User object
        election: Election object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Vote Confirmed - {election.name}'
        message = f"""
        Dear {user.get_full_name() or user.username},
        
        Your vote has been successfully recorded for: {election.name}
        
        Thank you for participating in the democratic process!
        
        Vote Details:
        - Election: {election.name}
        - Timestamp: {user.votes.filter(election=election).first().created.strftime('%B %d, %Y at %I:%M %p')}
        - Status: Confirmed and Encrypted
        
        Your vote is secure and anonymous. Results will be available once the election closes.
        
        Best regards,
        The Intikhab Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Vote confirmation sent to {user.email} for election {election.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send vote confirmation to {user.email}: {str(e)}")
        return False


def test_email_configuration():
    """
    Test the email configuration by sending a test email.
    
    Returns:
        bool: True if test email sent successfully, False otherwise
    """
    try:
        subject = 'Intikhab Email Configuration Test'
        message = 'This is a test email to verify SendGrid integration is working correctly.'
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Send to self for testing
            fail_silently=False,
        )
        
        logger.info("Test email sent successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return False