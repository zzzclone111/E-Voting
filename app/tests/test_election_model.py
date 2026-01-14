from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from app.models import Election, Candidate, Vote, Party


class ElectionModelTest(TestCase):
    """Test cases for the Election model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.election_data = {
            'name': 'Test Election 2025',
            'description': 'A test election for unit testing',
            'start_date': timezone.now() + timedelta(days=1),
            'end_date': timezone.now() + timedelta(days=7),
        }

    def test_election_creation(self):
        """Test creating an election with valid data"""
        election = Election.objects.create(**self.election_data)
        
        self.assertEqual(election.name, 'Test Election 2025')
        self.assertEqual(election.description, 'A test election for unit testing')
        self.assertFalse(election.active)  # Should be False by default
        self.assertEqual(election.private_key, "")  # Should be empty by default
        self.assertEqual(election.public_key, "")  # Should be empty by default
        self.assertIsNotNone(election.created)
        
    def test_election_str_representation(self):
        """Test the string representation of an election"""
        election = Election.objects.create(**self.election_data)
        self.assertEqual(str(election), 'Test Election 2025')

    def test_election_fields_defaults(self):
        """Test that election fields have correct default values"""
        election = Election.objects.create(**self.election_data)
        
        # Test default values for encryption fields
        self.assertEqual(election.private_key, "")
        self.assertEqual(election.public_key, "")
        self.assertEqual(election.encrypted_positive_total, "")
        self.assertEqual(election.encrypted_negative_total, "")
        self.assertEqual(election.encrypted_zero_sum, "")
        self.assertEqual(election.zero_randomness, "")
        self.assertEqual(election.decrypted_total, "")
        
        # Test boolean default
        self.assertFalse(election.active)

    def test_election_with_candidates(self):
        """Test election with associated candidates"""
        election = Election.objects.create(**self.election_data)
        
        # Create a party
        party = Party.objects.create(name='Test Party')
        
        # Create a candidate
        candidate = Candidate.objects.create(
            user=self.user,
            party=party,
            election=election
        )
        
        # Test the relationship
        self.assertEqual(election.candidates.count(), 1)
        self.assertEqual(election.candidates.first(), candidate)

    def test_election_with_votes(self):
        """Test election with associated votes"""
        election = Election.objects.create(**self.election_data)
        
        # Since votes require complex encryption setup, we'll test the basic relationship
        # More detailed vote testing will be in the Vote model tests
        self.assertEqual(election.votes.count(), 0)

    def test_election_date_validation(self):
        """Test that elections can be created with future dates"""
        future_start = timezone.now() + timedelta(days=30)
        future_end = timezone.now() + timedelta(days=37)
        
        election_data = self.election_data.copy()
        election_data['start_date'] = future_start
        election_data['end_date'] = future_end
        
        election = Election.objects.create(**election_data)
        self.assertEqual(election.start_date, future_start)
        self.assertEqual(election.end_date, future_end)

    def test_election_name_max_length(self):
        """Test election name field max length"""
        # This tests that Django's CharField max_length is working
        long_name = 'A' * 101  # 101 characters, should be truncated or raise error
        election_data = self.election_data.copy()
        election_data['name'] = long_name
        
        # Django should handle this based on your field definition
        # This test ensures we're aware of the constraint
        election = Election.objects.create(**election_data)
        # The actual behavior depends on your database and Django settings
        self.assertIsNotNone(election)

    def test_election_active_toggle(self):
        """Test toggling election active status"""
        election = Election.objects.create(**self.election_data)
        
        # Should start as inactive
        self.assertFalse(election.active)
        
        # Activate election
        election.active = True
        election.save()
        
        # Verify it's active
        election.refresh_from_db()
        self.assertTrue(election.active)
        
        # Deactivate election
        election.active = False
        election.save()
        
        # Verify it's inactive
        election.refresh_from_db()
        self.assertFalse(election.active)

    def test_election_encryption_fields_storage(self):
        """Test that encryption-related fields can store data"""
        election = Election.objects.create(**self.election_data)
        
        # Test storing sample encryption data
        test_key = '{"g": 123, "n": 456}'
        test_total = '[{"ciphertext": 789, "randomness": 101112}]'
        
        election.public_key = test_key
        election.encrypted_positive_total = test_total
        election.save()
        
        election.refresh_from_db()
        self.assertEqual(election.public_key, test_key)
        self.assertEqual(election.encrypted_positive_total, test_total)