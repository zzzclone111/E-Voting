from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

# Import views from the new organized structure
from app.views import (
    # Base views
    index, profile, terms, privacy, accessibility, contact, faqs, how,
    # Election views
    ElectionListView, ElectionDetailView, ElectionCreateView, ElectionUpdateView,
    # Candidate views
    CandidateCreateView, CandidateUpdateView, CandidateDeleteView, CandidateDetailView,
    # Vote views
    VoteView, CloseElectionView, StartElectionView, VerifyResultsView,
    # Invitation views
    send_invitations, manage_invitations, invitation_accept, 
    resend_invitation, cancel_invitation, process_pending_invitation,
    # Auth views
    CustomLoginView
)

admin.site.site_header = 'Election Management System'
admin.site.site_title = 'E-Voting'

urlpatterns = [
    # Base views
    path('', index, name='index'),
    path('profile', profile, name='profile'),
    
    # Legal pages
    path('terms', terms, name='terms'),
    path('privacy', privacy, name='privacy'),
    path('accessibility', accessibility, name='accessibility'),
    path('contact', contact, name='contact'),
    path('faqs', faqs, name='faqs'),
    path('how', how, name='how'),
    
    # Election management
    path('elections', ElectionListView.as_view(), name='election_list'),
    path('elections/create', ElectionCreateView.as_view(), name='create_election'),
    path('elections/<uuid:uuid>', ElectionDetailView.as_view(), name='election_detail'),
    path('elections/<uuid:uuid>/edit', ElectionUpdateView.as_view(), name='edit_election'),
    path('elections/<uuid:uuid>/close', CloseElectionView.as_view(), name='close_election'),
    path('elections/<uuid:uuid>/start', StartElectionView.as_view(), name='start_election'),
    
    # Candidate management
    path('elections/<uuid:uuid>/candidates/create', CandidateCreateView.as_view(), name='add_candidate'),
    path('candidates/<uuid:uuid>', CandidateDetailView.as_view(), name='candidate_detail'),
    path('candidates/<uuid:uuid>/edit', CandidateUpdateView.as_view(), name='edit_candidate'),
    path('candidates/<uuid:uuid>/delete', CandidateDeleteView.as_view(), name='delete_candidate'),
    
    # Voting and results
    path('candidates/<uuid:uuid>/vote', VoteView.as_view(), name='vote'),
    path('elections/<uuid:uuid>/verify-results', VerifyResultsView.as_view(), name='verify_results'),
    
    # Invitation management
    path('elections/<uuid:uuid>/invitations', manage_invitations, name='manage_invitations'),
    path('elections/<uuid:uuid>/invitations/send', send_invitations, name='send_invitations'),
    path('invitations/<uuid:uuid>/respond', invitation_accept, name='invitation_accept'),
    path('invitations/<uuid:uuid>/resend', resend_invitation, name='resend_invitation'),
    path('invitations/<uuid:uuid>/cancel', cancel_invitation, name='cancel_invitation'),
    path('process-invitation', process_pending_invitation, name='process_pending_invitation'),
    
    # Authentication
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
