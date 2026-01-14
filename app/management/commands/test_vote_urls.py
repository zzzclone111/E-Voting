from django.core.management.base import BaseCommand
from django.urls import reverse
from app.models import Election, Candidate

class Command(BaseCommand):
    help = 'Test that voting URLs work with the new nested structure'

    def handle(self, *args, **options):
        try:
            election = Election.objects.first()
            if not election:
                self.stdout.write("No elections found. Run seed command first.")
                return
                
            candidate = Candidate.objects.filter(election=election).first()
            if not candidate:
                self.stdout.write(f"No candidates found for election '{election.name}'. Run seed command first.")
                return
            
            # Test URL reversal
            vote_url = reverse('vote', kwargs={'election_pk': election.pk, 'pk': candidate.pk})
            
            self.stdout.write(self.style.SUCCESS("✅ Voting URL working correctly:"))
            self.stdout.write(f"  - Vote URL: {vote_url}")
            self.stdout.write(f"  - Election: {election.name}")
            self.stdout.write(f"  - Candidate: {candidate.user.get_full_name()}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error testing voting URLs: {e}"))