"""
Test configuration and utilities for the Intikhab election application.

This module provides common test utilities and configurations that can be used
across all test modules.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from app.models import Election, Party, Candidate, Vote


class BaseTestCase(TestCase):
    """Base test case with common setup for election app tests"""
    
    def setUp(self):
        """Set up common test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.voter_user = User.objects.create_user(
            username='voter',
            email='voter@example.com',
            password='voterpass123',
            first_name='Test',
            last_name='Voter'
        )
        
        self.candidate_user = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='candidatepass123',
            first_name='Test',
            last_name='Candidate'
        )
        
        # Create Citizens group
        self.citizens_group, created = Group.objects.get_or_create(name='Citizens')
        self.voter_user.groups.add(self.citizens_group)
        
        # Create test party
        self.test_party = Party.objects.create(
            name='Test Political Party'
        )
        
        # Create test election
        self.test_election = Election.objects.create(
            name='Test Election 2025',
            description='A comprehensive test election for unit testing',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=7),
            public_key='{"g": 123456, "n": 789012}',
            private_key='{"phi": 345678}',
            active=False
        )
        
        # Create test candidate
        self.test_candidate = Candidate.objects.create(
            user=self.candidate_user,
            party=self.test_party,
            election=self.test_election
        )

    def create_test_vote(self, user=None, election=None, ballot_data=None):
        """Helper method to create test votes"""
        user = user or self.voter_user
        election = election or self.test_election
        ballot_data = ballot_data or '[1, 0, 0]'
        
        return Vote.objects.create(
            user=user,
            election=election,
            ballot=ballot_data,
            hashed='test_hash_' + user.username
        )

    def create_future_election(self, name_suffix="Future"):
        """Helper method to create elections in the future"""
        return Election.objects.create(
            name=f'Test Election {name_suffix}',
            description=f'Future election for testing - {name_suffix}',
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=37),
            public_key='{"g": 111111, "n": 222222}',
            private_key='{"phi": 333333}',
            active=False
        )

    def create_past_election(self, name_suffix="Past"):
        """Helper method to create elections in the past"""
        return Election.objects.create(
            name=f'Test Election {name_suffix}',
            description=f'Past election for testing - {name_suffix}',
            start_date=timezone.now() - timedelta(days=7),
            end_date=timezone.now() - timedelta(days=1),
            public_key='{"g": 444444, "n": 555555}',
            private_key='{"phi": 666666}',
            active=False
        )

    def create_additional_candidate(self, username_suffix="2"):
        """Helper method to create additional candidates"""
        user = User.objects.create_user(
            username=f'candidate{username_suffix}',
            email=f'candidate{username_suffix}@example.com',
            password='candidatepass123',
            first_name=f'Candidate',
            last_name=f'Number{username_suffix}'
        )
        
        return Candidate.objects.create(
            user=user,
            party=self.test_party,
            election=self.test_election
        )


class TestDataMixin:
    """Mixin providing test data creation methods"""
    
    @staticmethod
    def get_sample_encrypted_ballot():
        """Return a sample encrypted ballot for testing"""
        return '[{"ciphertext": 12345, "randomness": 67890}, {"ciphertext": 11111, "randomness": 22222}]'
    
    @staticmethod
    def get_sample_public_key():
        """Return a sample public key for testing"""
        return '{"g": 98765, "n": 43210, "bits": 2048}'
    
    @staticmethod
    def get_sample_private_key():
        """Return a sample private key for testing"""
        return '{"phi": 54321, "mu": 98765}'
    
    @staticmethod
    def get_sample_vote_hash():
        """Return a sample vote hash for testing"""
        import hashlib
        test_data = "sample_vote_data_for_testing"
        return hashlib.sha256(test_data.encode()).hexdigest()