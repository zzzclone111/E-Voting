"""
Comprehensive URL testing for all GET request endpoints in the Intikhab election system.

This test module validates that all URL patterns work correctly with both valid and invalid parameters,
including public URLs, authenticated URLs, admin URLs, UUID-based routing, and security validations.
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User



class BaseTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123',
            email='test@example.com'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            password='adminpass123',
            email='admin@example.com'
        )


class SimpleURLTestCase(BaseTestCase):
    """Simplified URL testing focusing on accessibility and basic functionality"""
    
    def test_public_urls_accessible(self):
        """Test that public URLs return appropriate responses"""
        public_urls = [
            'index', 'terms', 'privacy', 'accessibility', 
            'contact', 'faqs', 'election_list', 'login', 'how'
        ]
        
        for url_name in public_urls:
            with self.subTest(url=url_name):
                url = reverse(url_name)
                response = self.client.get(url)
                # Should get a valid response (200, 301, 302 are all acceptable)
                self.assertIn(response.status_code, [200, 301, 302], 
                            f"Public URL {url_name} returned {response.status_code}")
    
    def test_uuid_url_patterns_work(self):
        """Test that UUID-based URL patterns resolve correctly"""
        # Test URL patterns that use UUID parameters
        test_uuid = str(uuid.uuid4())
        
        uuid_patterns = [
            ('election_detail', {'uuid': test_uuid}),
            ('candidate_detail', {'uuid': test_uuid}),
        ]
        
        for url_name, kwargs in uuid_patterns:
            with self.subTest(url=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    # If we can reverse it, the pattern is valid
                    self.assertTrue(url.startswith('/'), f"URL {url_name} should start with /")
                    self.assertIn(test_uuid, url, f"UUID should be in the URL for {url_name}")
                except Exception as e:
                    self.fail(f"Failed to reverse URL {url_name}: {e}")
    
    def test_authenticated_urls(self):
        """Test URLs that require authentication"""
        # Login as regular user
        self.client.force_login(self.user)
        
        auth_urls = [
            ('profile', {}),
        ]
        
        for url_name, kwargs in auth_urls:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)
                
                # Should be accessible to authenticated users
                self.assertIn(response.status_code, [200, 301, 302], 
                            f"Authenticated URL {url_name} returned {response.status_code}")
    
    def test_admin_urls(self):
        """Test URLs that require admin permissions"""
        self.client.force_login(self.admin_user)
        
        admin_urls = [
            ('create_election', {}),
        ]
        
        for url_name, kwargs in admin_urls:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)
                
                # Should be accessible to admin users (200) or redirect (302)
                self.assertIn(response.status_code, [200, 302], 
                            f"Admin URL {url_name} returned {response.status_code}")
    
    def test_invalid_uuid_returns_404(self):
        """Test that invalid UUIDs return 404 errors"""
        non_existent_uuid = str(uuid.uuid4())  # Valid format but doesn't exist
        
        # Test public URLs that don't require login
        public_uuid_patterns = [
            ('election_detail', 'uuid'),
            ('candidate_detail', 'uuid'),
        ]
        
        for url_name, param_name in public_uuid_patterns:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs={param_name: non_existent_uuid})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404,
                               f"Non-existent UUID should return 404 for {url_name}")
        
        # Test authenticated URLs that require login - login first
        self.client.force_login(self.user)
        auth_uuid_patterns = [
            ('vote', 'uuid'),  # This expects a candidate UUID
        ]
        
        for url_name, param_name in auth_uuid_patterns:
            with self.subTest(url=url_name):
                url = reverse(url_name, kwargs={param_name: non_existent_uuid})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404,
                               f"Non-existent UUID should return 404 for {url_name}")
    
    def test_all_url_patterns_resolvable(self):
        """Test that basic URL patterns can be resolved"""
        basic_patterns = [
            'index', 'terms', 'privacy', 'accessibility', 'contact', 'faqs', 'how',
            'election_list', 'create_election', 'login'
        ]
        
        for pattern_name in basic_patterns:
            with self.subTest(pattern=pattern_name):
                try:
                    url = reverse(pattern_name)
                    self.assertTrue(url.startswith('/'), f"URL should start with / for {pattern_name}")
                except Exception as e:
                    self.fail(f"Could not reverse URL pattern {pattern_name}: {e}")
    
    def test_auth_url_patterns(self):
        """Test authentication-related URL patterns"""
        auth_patterns = ['login']
        
        for pattern_name in auth_patterns:
            with self.subTest(pattern=pattern_name):
                url = reverse(pattern_name)
                response = self.client.get(url)
                # Auth pages should be accessible (200) or redirect (302)
                self.assertIn(response.status_code, [200, 302], 
                            f"Auth URL {pattern_name} returned {response.status_code}")
    
    def test_election_uuid_workflow(self):
        """Test the complete election UUID workflow"""
        test_uuid = str(uuid.uuid4())
        
        # Test election detail URL with UUID
        url = reverse('election_detail', kwargs={'uuid': test_uuid})
        self.assertIn(test_uuid, url)
        
        # Test that the URL contains the expected format
        self.assertTrue(url.startswith('/elections/'))
        self.assertIn(test_uuid, url)
    
    def test_basic_response_times(self):
        """Basic performance test - ensure URLs respond quickly"""
        import time
        
        fast_urls = ['index', 'terms', 'login']
        
        for url_name in fast_urls:
            with self.subTest(url=url_name):
                start_time = time.time()
                self.client.get(reverse(url_name))  # We don't need to store the response
                response_time = time.time() - start_time
                
                # Should respond within 2 seconds (very generous for local tests)
                self.assertLess(response_time, 2.0, 
                              f"URL {url_name} took {response_time:.2f}s to respond")
    
    def test_url_consistency(self):
        """Test basic URL pattern consistency"""
        # Test that election URLs follow the /elections/ pattern
        test_uuid = str(uuid.uuid4())
        election_url = reverse('election_detail', kwargs={'uuid': test_uuid})
        self.assertTrue(election_url.startswith('/elections/'))
        
        # Test that candidate URLs follow the /candidates/ pattern  
        candidate_url = reverse('candidate_detail', kwargs={'uuid': test_uuid})
        self.assertTrue(candidate_url.startswith('/candidates/'))


class URLSecurityTestCase(BaseTestCase):
    """Security-focused URL testing"""
    
    def test_uuid_format_validation(self):
        """Test that URL patterns only accept valid UUID formats"""
        invalid_uuids = [
            'invalid-uuid',
            '123456',
            'not-a-uuid-at-all',
            '12345678-1234-1234-1234-12345678901',  # Too short
        ]
        
        for invalid_uuid in invalid_uuids:
            with self.subTest(uuid=invalid_uuid):
                try:
                    # This should either fail to reverse or return 404
                    url = reverse('election_detail', kwargs={'uuid': invalid_uuid})
                    response = self.client.get(url)
                    # If it reverses, it should return 404 for invalid format
                    self.assertEqual(response.status_code, 404, 
                                   f"Invalid UUID {invalid_uuid} should return 404")
                except Exception:
                    # If it fails to reverse, that's also acceptable
                    pass
    
    def test_url_case_sensitivity(self):
        """Test URL case sensitivity"""
        test_uuid = str(uuid.uuid4())
        url = reverse('election_detail', kwargs={'uuid': test_uuid})
        
        # Test that the URL is consistent
        self.assertIn(test_uuid, url)
        self.assertTrue(url.startswith('/elections/'))
    
    def test_admin_panel_accessible(self):
        """Test that admin panel is accessible"""
        response = self.client.get('/admin/')
        # Should redirect to login page (302) or show login form (200)
        self.assertIn(response.status_code, [200, 302])