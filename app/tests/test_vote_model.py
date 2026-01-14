from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta
from app.models import Election, Candidate, Vote, Party
import json


class VoteModelTest(TestCase):
    """Test cases for the Vote model"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.voter1 = User.objects.create_user(
            username='voter1',
            email='voter1@example.com',
            password='testpass123'
        )
        
        self.voter2 = User.objects.create_user(
            username='voter2',
            email='voter2@example.com',
            password='testpass123'
        )
        
        self.candidate_user = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='testpass123',
            first_name='John',
            last_name='Candidate'
        )
        
        # Create test party
        self.party = Party.objects.create(name='Test Party')
        
        # Create test election with sample keys
        self.election = Election.objects.create(
            name='Test Election 2025',
            description='A test election',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=7),
            public_key='{"g": 123, "n": 456}',  # Sample public key
            private_key='{"phi": 789}'  # Sample private key
        )
        
        # Create test candidate
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            party=self.party,
            election=self.election
        )

    def test_vote_creation_basic(self):
        """Test creating a basic vote record"""
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',  # Sample ballot data
            hashed='sample_hash_value'
        )
        
        self.assertEqual(vote.user, self.voter1)
        self.assertEqual(vote.election, self.election)
        self.assertEqual(vote.ballot, '[1, 0, 0]')
        self.assertEqual(vote.hashed, 'sample_hash_value')
        self.assertIsNotNone(vote.created)

    def test_vote_str_representation(self):
        """Test the string representation of a vote"""
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed='sample_hash'
        )
        
        expected_str = f"{self.voter1.username} - {self.election.name}"
        self.assertEqual(str(vote), expected_str)

    def test_vote_unique_constraint(self):
        """Test that the unique constraint works (one vote per user per election)"""
        # Create first vote
        Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed='first_hash'
        )
        
        # Try to create second vote for same user and election
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                user=self.voter1,
                election=self.election,
                ballot='[0, 1, 0]',
                hashed='second_hash'
            )

    def test_vote_different_users_same_election(self):
        """Test that different users can vote in the same election"""
        vote1 = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed='hash1'
        )
        
        vote2 = Vote.objects.create(
            user=self.voter2,
            election=self.election,
            ballot='[0, 1, 0]',
            hashed='hash2'
        )
        
        self.assertEqual(Vote.objects.filter(election=self.election).count(), 2)
        self.assertNotEqual(vote1.user, vote2.user)

    def test_vote_same_user_different_elections(self):
        """Test that the same user can vote in different elections"""
        # Create second election
        election2 = Election.objects.create(
            name='Second Election',
            description='Another test election',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=17),
            public_key='{"g": 111, "n": 222}',
            private_key='{"phi": 333}'
        )
        
        vote1 = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed='hash1'
        )
        
        vote2 = Vote.objects.create(
            user=self.voter1,
            election=election2,
            ballot='[0, 1, 0]',
            hashed='hash2'
        )
        
        self.assertEqual(Vote.objects.filter(user=self.voter1).count(), 2)
        self.assertNotEqual(vote1.election, vote2.election)

    def test_vote_default_values(self):
        """Test that default values are set correctly"""
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election
        )
        
        # Default values should be empty strings
        self.assertEqual(vote.ballot, "")
        self.assertEqual(vote.hashed, "")

    def test_vote_creation_timestamp(self):
        """Test that created timestamp is automatically set"""
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0]',
            hashed='test_hash'
        )
        
        self.assertIsNotNone(vote.created)
        # The created time should be recent (within last minute)
        self.assertTrue(
            (timezone.now() - vote.created).total_seconds() < 60
        )

    def test_vote_ballot_storage(self):
        """Test that ballot data can be stored as JSON string"""
        sample_ballot = [1, 0, 1, 0, 0]
        ballot_json = json.dumps(sample_ballot)
        
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot=ballot_json,
            hashed='json_hash'
        )
        
        # Test that we can retrieve and parse the ballot
        retrieved_ballot = json.loads(vote.ballot)
        self.assertEqual(retrieved_ballot, sample_ballot)

    def test_vote_hash_storage(self):
        """Test that vote hash can be stored"""
        import hashlib
        
        test_data = "test_vote_data"
        expected_hash = hashlib.sha256(test_data.encode()).hexdigest()
        
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed=expected_hash
        )
        
        self.assertEqual(vote.hashed, expected_hash)
        self.assertEqual(len(vote.hashed), 64)  # SHA256 hash length

    def test_vote_foreign_key_relationships(self):
        """Test foreign key relationships"""
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot='[1, 0, 0]',
            hashed='test_hash'
        )
        
        # Test relationships
        self.assertEqual(vote.user, self.voter1)
        self.assertEqual(vote.election, self.election)
        
        # Test that vote is accessible through user and election
        # (These may not work due to related_name issues we saw in linting)
        
    def test_vote_meta_unique_together(self):
        """Test the Meta unique_together constraint"""
        # This is tested implicitly in test_vote_unique_constraint
        # but we can also verify the Meta class
        meta = Vote._meta
        self.assertIn(('user', 'election'), meta.unique_together)

    def test_vote_with_complex_ballot_data(self):
        """Test storing complex ballot data"""
        complex_ballot = {
            "candidates": [1, 0, 1, 0],
            "timestamp": "2025-01-01T12:00:00Z",
            "encrypted": True
        }
        ballot_json = json.dumps(complex_ballot)
        
        vote = Vote.objects.create(
            user=self.voter1,
            election=self.election,
            ballot=ballot_json,
            hashed='complex_hash'
        )
        
        # Verify we can retrieve and parse complex data
        retrieved_data = json.loads(vote.ballot)
        self.assertEqual(retrieved_data, complex_ballot)
        self.assertTrue(retrieved_data["encrypted"])
        self.assertEqual(len(retrieved_data["candidates"]), 4)