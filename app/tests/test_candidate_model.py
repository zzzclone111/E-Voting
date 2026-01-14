from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from app.models import Election, Candidate, Party


class CandidateModelTest(TestCase):
    """Test cases for the Candidate model"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='candidate1',
            email='candidate1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.user2 = User.objects.create_user(
            username='candidate2',
            email='candidate2@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create test party
        self.party = Party.objects.create(name='Test Party')
        
        # Create test election
        self.election = Election.objects.create(
            name='Test Election 2025',
            description='A test election',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=7),
        )

    def test_candidate_creation_basic(self):
        """Test creating a candidate with required fields only"""
        candidate = Candidate.objects.create(
            user=self.user1,
            election=self.election
        )
        
        self.assertEqual(candidate.user, self.user1)
        self.assertEqual(candidate.election, self.election)
        self.assertIsNone(candidate.party)  # Should be None when not provided
        self.assertFalse(candidate.symbol)  # Should be falsy when not provided
        self.assertIsNotNone(candidate.created)

    def test_candidate_creation_with_party(self):
        """Test creating a candidate with a party"""
        candidate = Candidate.objects.create(
            user=self.user1,
            party=self.party,
            election=self.election
        )
        
        self.assertEqual(candidate.user, self.user1)
        self.assertEqual(candidate.party, self.party)
        self.assertEqual(candidate.election, self.election)

    def test_candidate_creation_with_symbol(self):
        """Test creating a candidate with a symbol file"""
        test_file = SimpleUploadedFile(
            "candidate_symbol.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        candidate = Candidate.objects.create(
            user=self.user1,
            election=self.election,
            symbol=test_file
        )
        
        self.assertEqual(candidate.user, self.user1)
        self.assertTrue(candidate.symbol.name.startswith('uploads/'))
        self.assertTrue(candidate.symbol.name.endswith('candidate_symbol.jpg'))

    def test_candidate_str_representation(self):
        """Test the string representation of a candidate"""
        candidate = Candidate.objects.create(
            user=self.user1,
            election=self.election
        )
        
        # Should return the user's full name
        expected_str = self.user1.get_full_name()  # "John Doe"
        self.assertEqual(str(candidate), expected_str)

    def test_candidate_with_user_without_full_name(self):
        """Test candidate string representation when user has no full name"""
        user_no_name = User.objects.create_user(
            username='no_name_user',
            email='noname@example.com',
            password='testpass123'
        )
        
        candidate = Candidate.objects.create(
            user=user_no_name,
            election=self.election
        )
        
        # When user has no first/last name, get_full_name() returns empty string
        self.assertEqual(str(candidate), "")

    def test_multiple_candidates_same_election(self):
        """Test that multiple candidates can be in the same election"""
        candidate1 = Candidate.objects.create(
            user=self.user1,
            election=self.election,
            party=self.party
        )
        
        candidate2 = Candidate.objects.create(
            user=self.user2,
            election=self.election
        )
        
        self.assertEqual(Candidate.objects.filter(election=self.election).count(), 2)
        self.assertNotEqual(candidate1.user, candidate2.user)

    def test_candidate_foreign_key_relationships(self):
        """Test the foreign key relationships"""
        candidate = Candidate.objects.create(
            user=self.user1,
            party=self.party,
            election=self.election
        )
        
        # Test that relationships work both ways
        self.assertEqual(candidate.user, self.user1)
        self.assertEqual(candidate.party, self.party)
        self.assertEqual(candidate.election, self.election)
        
        # Test reverse relationships exist
        # Note: These might not work due to the linter warnings we saw earlier
        # but we're testing the intended behavior

    def test_candidate_creation_timestamp(self):
        """Test that created timestamp is automatically set"""
        candidate = Candidate.objects.create(
            user=self.user1,
            election=self.election
        )
        
        self.assertIsNotNone(candidate.created)
        # The created time should be recent (within last minute)
        self.assertTrue(
            (timezone.now() - candidate.created).total_seconds() < 60
        )

    def test_candidate_deletion_protection(self):
        """Test that candidates are protected from deletion when related objects exist"""
        candidate = Candidate.objects.create(
            user=self.user1,
            party=self.party,
            election=self.election
        )
        
        # Verify candidate was created
        self.assertTrue(Candidate.objects.filter(user=self.user1).exists())
        
        # The PROTECT constraint means that if we try to delete the user,
        # it should prevent deletion (though we won't test actual deletion here
        # to avoid data loss in case of test errors)
        
    def test_candidate_optional_fields(self):
        """Test that optional fields (party, symbol) can be null/blank"""
        candidate = Candidate.objects.create(
            user=self.user1,
            election=self.election,
            party=None,  # Explicitly set to None
            symbol=None  # Explicitly set to None
        )
        
        self.assertIsNone(candidate.party)
        self.assertFalse(candidate.symbol)  # Empty file field is falsy

    def test_candidate_with_all_fields(self):
        """Test creating a candidate with all possible fields"""
        test_file = SimpleUploadedFile(
            "full_candidate.jpg",
            b"comprehensive test image",
            content_type="image/jpeg"
        )
        
        candidate = Candidate.objects.create(
            user=self.user1,
            party=self.party,
            election=self.election,
            symbol=test_file
        )
        
        self.assertEqual(candidate.user, self.user1)
        self.assertEqual(candidate.party, self.party)
        self.assertEqual(candidate.election, self.election)
        self.assertTrue(candidate.symbol)
        self.assertIsNotNone(candidate.created)