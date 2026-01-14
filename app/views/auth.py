"""
Authentication views for custom login redirects
"""
from django.contrib.auth.views import LoginView


class CustomLoginView(LoginView):
    """
    Custom login view that redirects admin users to /admin
    and regular users to the homepage
    """
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        """
        Redirect admin users to /admin, others to homepage
        """
        user = self.request.user
        
        # Check if user is staff/admin
        if user.is_staff or user.is_superuser:
            return '/admin/'
        
        # Regular users go to homepage
        return '/'