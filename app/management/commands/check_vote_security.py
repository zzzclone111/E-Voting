"""
Management command to check vote encryption status
"""
from django.core.management.base import BaseCommand
from app.models import Vote, Election, Candidate


class Command(BaseCommand):
    help = 'Check vote encryption status across all elections'
    
    def add_arguments(self, parser):
        parser.add_argument('--election', type=int, help='Check specific election ID')
        parser.add_argument('--insecure-only', action='store_true', help='Show only insecure votes')
    
    def handle(self, *args, **options):
        if options['election']:
            elections = Election.objects.filter(id=options['election'])
        else:
            elections = Election.objects.all()
        
        total_votes = 0
        insecure_votes = 0
        
        for election in elections:
            votes = Vote.objects.filter(election=election)
            election_insecure = 0
            
            self.stdout.write(f"\n=== Election: {election.name} (ID: {election.id}) ===")
            
            if not votes.exists():
                self.stdout.write("No votes found.")
                continue
            
            for vote in votes:
                total_votes += 1
                is_insecure = self._is_vote_insecure(vote)
                
                if is_insecure:
                    insecure_votes += 1
                    election_insecure += 1
                
                if not options['insecure_only'] or is_insecure:
                    security_status = "INSECURE" if is_insecure else "SECURE"
                    self.stdout.write(
                        f"  {vote.user.username}: {security_status} - "
                        f"Ballot: {str(vote.ballot)[:50]}{'...' if len(str(vote.ballot)) > 50 else ''}"
                    )
            
            if election_insecure > 0:
                self.stdout.write(
                    self.style.ERROR(f"  ⚠️  {election_insecure} insecure votes found!")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ All {votes.count()} votes are secure")
                )
        
        # Summary
        self.stdout.write(f"\n=== SUMMARY ===")
        self.stdout.write(f"Total votes checked: {total_votes}")
        if insecure_votes > 0:
            self.stdout.write(
                self.style.ERROR(f"Insecure votes: {insecure_votes} ({insecure_votes/total_votes*100:.1f}%)")
            )
            self.stdout.write(
                self.style.WARNING("⚠️  CRITICAL: Ballot secrecy is compromised!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ All votes are properly encrypted")
            )
    
    def _is_vote_insecure(self, vote):
        """Check if a vote is insecurely stored"""
        ballot_str = str(vote.ballot)
        
        # Check if ballot contains plain text candidate ID (format: "candidate_id:hash")
        if ':' in ballot_str and not ballot_str.startswith('['):
            # This is the old insecure format
            return True
        
        # Check if ballot is a properly encrypted list/array
        if ballot_str.startswith('[') and ballot_str.endswith(']'):
            try:
                # Should be a list of encrypted values (very long integers), not plain integers
                import ast
                ballot_list = ast.literal_eval(ballot_str)
                if isinstance(ballot_list, list) and len(ballot_list) > 0:
                    # Check if all elements are very large integers (encrypted values)
                    # Encrypted values should be much larger than candidate IDs
                    for item in ballot_list:
                        if isinstance(item, int):
                            # If integer is small (< 1000), it's likely a plain candidate ID
                            # If integer is very large (> 1000), it's likely encrypted
                            if item < 1000:
                                return True
                        else:
                            # Non-integer in ballot list is suspicious
                            return True
                    # All elements are large integers - this is properly encrypted
                    return False
            except (ValueError, SyntaxError):
                # If we can't parse the ballot, assume it's secure
                return False
        
        # If ballot format is unrecognized, assume it's secure
        return False