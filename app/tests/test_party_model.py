from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from app.models import Party
import tempfile
import os


class PartyModelTest(TestCase):
    """Test cases for the Party model"""

    def setUp(self):
        """Set up test data"""
        self.party_data = {
            'name': 'Test Political Party',
        }

    def test_party_creation(self):
        """Test creating a party with valid data"""
        party = Party.objects.create(**self.party_data)
        
        self.assertEqual(party.name, 'Test Political Party')
        self.assertIsNotNone(party.created)

    def test_party_str_representation(self):
        """Test the string representation of a party"""
        party = Party.objects.create(**self.party_data)
        self.assertEqual(str(party), 'Test Political Party')

    def test_party_meta_verbose_names(self):
        """Test that the meta verbose names are set correctly"""
        self.assertEqual(Party._meta.verbose_name, 'Party')
        self.assertEqual(Party._meta.verbose_name_plural, 'Parties')

    def test_party_with_symbol(self):
        """Test creating a party with a symbol file"""
        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test_symbol.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        party = Party.objects.create(
            name='Party with Symbol',
            symbol=test_file
        )
        
        self.assertEqual(party.name, 'Party with Symbol')
        self.assertTrue(party.symbol.name.startswith('uploads/'))
        self.assertTrue(party.symbol.name.endswith('test_symbol.jpg'))

    def test_party_without_symbol(self):
        """Test creating a party without a symbol"""
        party = Party.objects.create(name='Party without Symbol')
        
        self.assertEqual(party.name, 'Party without Symbol')
        # Symbol field should be empty/falsy when not provided
        self.assertFalse(party.symbol)

    def test_party_name_uniqueness(self):
        """Test that multiple parties can have different names"""
        party1 = Party.objects.create(name='First Party')
        party2 = Party.objects.create(name='Second Party')
        
        self.assertEqual(Party.objects.count(), 2)
        self.assertNotEqual(party1.name, party2.name)

    def test_party_creation_timestamp(self):
        """Test that created timestamp is automatically set"""
        party = Party.objects.create(**self.party_data)
        
        self.assertIsNotNone(party.created)
        # The created time should be recent (within last minute)
        from django.utils import timezone
        self.assertTrue(
            (timezone.now() - party.created).total_seconds() < 60
        )

    def test_party_name_max_length(self):
        """Test party name field constraints"""
        # Test with exactly 100 characters (the max_length)
        long_name = 'A' * 100
        party = Party.objects.create(name=long_name)
        self.assertEqual(len(party.name), 100)
        
    def test_party_relationships(self):
        """Test that party can be referenced by candidates"""
        party = Party.objects.create(**self.party_data)
        
        # Test that party exists and can be used in relationships
        self.assertTrue(Party.objects.filter(id=party.id).exists())
        self.assertEqual(party.id, Party.objects.get(name=self.party_data['name']).id)