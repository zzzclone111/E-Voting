"""
User model extensions for role-based permissions
"""
from django.contrib.auth.models import User


# Extend User model with role-checking methods
def is_election_creator(self):
    """Check if user can create elections (superuser or Officials group member)"""
    return self.is_superuser or self.groups.filter(name='Officials').exists()


def is_election_manager(self):
    """Check if user can manage elections (superuser or Officials/Managers group member)"""
    return (self.is_superuser or 
            self.groups.filter(name__in=['Officials', 'Managers']).exists())


def is_vote_counter(self):
    """Check if user can count votes and view results"""
    return (self.is_superuser or 
            self.groups.filter(name__in=['Officials', 'Counters']).exists())


def can_close_elections(self):
    """Check if user can close elections (superuser or Officials only for security)"""
    return self.is_superuser or self.groups.filter(name='Officials').exists()


def can_manage_candidates(self):
    """Check if user can add/remove candidates"""
    return (self.is_superuser or 
            self.groups.filter(name__in=['Officials', 'Managers']).exists())


def can_view_results(self):
    """Check if user can view election results"""
    return (self.is_superuser or 
            self.groups.filter(name__in=['Officials', 'Counters', 'Viewers']).exists())


def get_role_display(self):
    """Get user's primary role display name"""
    if self.is_superuser:
        return "System Administrator"
    
    user_groups = list(self.groups.values_list('name', flat=True))
    
    if 'Officials' in user_groups:
        return "Election Official"
    elif 'Managers' in user_groups:
        return "Election Manager"
    elif 'Counters' in user_groups:
        return "Vote Counter"
    elif 'Viewers' in user_groups:
        return "Results Viewer"
    else:
        return "Voter"


def get_all_roles(self):
    """Get all roles/groups the user belongs to"""
    roles = []
    if self.is_superuser:
        roles.append("System Administrator")
    
    group_role_mapping = {
        'Officials': 'Election Official',
        'Managers': 'Election Manager', 
        'Counters': 'Vote Counter',
        'Viewers': 'Results Viewer'
    }
    
    for group in self.groups.all():
        if group.name in group_role_mapping:
            roles.append(group_role_mapping[group.name])
    
    if not roles:
        roles.append("Voter")
    
    return roles


def has_election_permissions(self):
    """Check if user has any election management permissions"""
    return (self.is_superuser or 
            self.groups.filter(name__in=['Officials', 'Managers', 'Counters']).exists())


# Add methods to User model
User.add_to_class('is_election_creator', is_election_creator)
User.add_to_class('is_election_manager', is_election_manager)
User.add_to_class('is_vote_counter', is_vote_counter)
User.add_to_class('can_close_elections', can_close_elections)
User.add_to_class('can_manage_candidates', can_manage_candidates)
User.add_to_class('can_view_results', can_view_results)
User.add_to_class('get_role_display', get_role_display)
User.add_to_class('get_all_roles', get_all_roles)
User.add_to_class('has_election_permissions', has_election_permissions)