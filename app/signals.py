from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from allauth.account.signals import user_signed_up
from .email_utils import send_welcome_email


@receiver(post_save, sender=User)
def assign_user_to_citizens_group(sender, instance, created, **kwargs):
    """
    Automatically assign new users to the Citizens group when they are created.
    This works for both regular Django user creation and OAuth signups.
    """
    if created:
        # Get or create the Citizens group
        citizens_group, group_created = Group.objects.get_or_create(name='Citizens')
        
        # Add the user to the Citizens group
        instance.groups.add(citizens_group)
        
        # Send welcome email if user has an email address
        if instance.email:
            send_welcome_email(instance)
        
        print(f"User {instance.username} has been added to the Citizens group.")


@receiver(user_signed_up)
def assign_oauth_user_to_citizens_group(sender, request, user, **kwargs):
    """
    Additional handler specifically for OAuth signups through django-allauth.
    This ensures OAuth users are also assigned to the Citizens group.
    """
    # Get or create the Citizens group
    citizens_group, group_created = Group.objects.get_or_create(name='Citizens')
    
    # Add the user to the Citizens group
    user.groups.add(citizens_group)
    
    # Send welcome email for OAuth users
    if user.email:
        send_welcome_email(user)
    
    print(f"OAuth user {user.username} has been added to the Citizens group.")