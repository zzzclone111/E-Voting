from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from app.models import Election, Candidate, Party, Vote, Profile
from app.encryption import Encryption, Ciphertext
import json
from app.actions.elections_actions import start_election, end_election

# Register your models here.
class UserAdmin(BaseUserAdmin):
    """Custom User admin with group information"""
    list_display = list(BaseUserAdmin.list_display) + ['get_groups_display']
    list_filter = list(BaseUserAdmin.list_filter) + ['groups']
    
    def get_groups_display(self, obj):
        """Display user's groups as comma-separated list"""
        groups = obj.groups.all()
        if groups:
            return ', '.join([group.name for group in groups])
        return 'No groups'
    get_groups_display.short_description = 'Groups'

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_public', 'active', 'created')

    actions = [start_election, end_election]

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('user', 'party', 'election', 'created')

class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')

class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'election', 'ballot', 'created', 'hashed')
    # readonly_fields = ('created', 'user', 'election', 'ballot')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_display_name', 'get_age', 'location', 'gender', 'created')
    list_filter = ('gender', 'created')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location')
    readonly_fields = ('created', 'updated')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'avatar')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'location', 'gender')
        }),
        ('Profile Content', {
            'fields': ('profile', 'manifesto')
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Election, ElectionAdmin)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(Party, PartyAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Profile, ProfileAdmin)
