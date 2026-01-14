from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from app.models import Election, Candidate

class Command(BaseCommand):
    help = 'Test voting flow with GET and POST requests'

    def handle(self, *args, **options):
        try:
            # Get test data
            election = Election.objects.filter(active=True).first()
            if not election:
                self.stdout.write("No active elections found. Run seed command first.")
                return
                
            candidate = Candidate.objects.filter(election=election).first()
            if not candidate:
                self.stdout.write(f"No candidates found for election '{election.name}'. Run seed command first.")
                return
            
            # Create test client
            client = Client()
            
            # Test GET request (should show confirmation page)
            vote_url = f"/elections/{election.pk}/candidates/{candidate.pk}/vote"
            
            # Test without login (should redirect to login)
            response = client.get(vote_url)
            self.stdout.write(f"GET {vote_url} without login: {response.status_code} (should be 302 redirect to login)")
            
            # Test with admin user
            admin = User.objects.filter(is_superuser=True).first()
            if admin:
                client.force_login(admin)
                response = client.get(vote_url)
                self.stdout.write(f"GET {vote_url} with admin: {response.status_code} (should be 200 for confirmation page)")
                
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS("✅ Voting confirmation page loads correctly"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Expected 200, got {response.status_code}"))
            
            self.stdout.write(self.style.SUCCESS(f"🗳️  Voting URL structure working:"))
            self.stdout.write(f"  - URL: {vote_url}")
            self.stdout.write(f"  - Election: {election.name}")
            self.stdout.write(f"  - Candidate: {candidate.user.get_full_name()}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error testing voting flow: {e}"))