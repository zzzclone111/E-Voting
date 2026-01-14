"""
Management command to calculate and display election results
"""
from django.core.management.base import BaseCommand
from app.models import Election, Vote, Candidate
import json
from collections import defaultdict


class Command(BaseCommand):
    help = 'Calculate and display election results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--election-id',
            type=int,
            help='Calculate results for a specific election ID',
        )
        parser.add_argument(
            '--all-closed',
            action='store_true',
            help='Show results for all closed elections',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🗳️  ELECTION RESULTS CALCULATOR')
        )
        self.stdout.write('=' * 60)

        if options['election_id']:
            try:
                election = Election.objects.get(id=options['election_id'])
                self.calculate_results_for_election(election)
            except Election.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Election with ID {options["election_id"]} not found')
                )
        elif options['all_closed']:
            closed_elections = Election.objects.filter(closed_at__isnull=False)
            if not closed_elections.exists():
                self.stdout.write(
                    self.style.WARNING('No closed elections found')
                )
                return
            
            for election in closed_elections.order_by('-closed_at'):
                self.calculate_results_for_election(election)
                self.stdout.write('-' * 40)
        else:
            self.stdout.write(
                self.style.WARNING('Please specify --election-id or --all-closed')
            )
            self.stdout.write(
                'Usage: python manage.py calculate_results --election-id 47'
            )
            self.stdout.write(
                '   or: python manage.py calculate_results --all-closed'
            )

    def calculate_results_for_election(self, election):
        """Calculate and display results for a specific election"""
        self.stdout.write(f'\n🏛️  Election: {election.name}')
        self.stdout.write(f'   ID: {election.id}')
        
        status_info = election.get_status_display()
        self.stdout.write(f'   Status: {status_info["text"]}')
        
        if not election.can_show_results():
            self.stdout.write(
                self.style.WARNING('   ⚠️  Results not available (election not closed)')
            )
            return
        
        # Get election results using the model method
        results_data = election.get_results()
        
        if not results_data:
            self.stdout.write(
                self.style.WARNING('   ⚠️  No votes or candidates found')
            )
            return
        
        self.stdout.write(f'   Total Votes: {results_data["total_votes"]}')
        self.stdout.write(f'   Candidates: {results_data["candidates_count"]}')
        self.stdout.write('')
        self.stdout.write('   📊 RESULTS:')
        
        for i, result in enumerate(results_data['results'], 1):
            candidate = result['candidate']
            votes = result['votes']
            percentage = result['percentage']
            party = result['party']
            
            # Add medal emoji for top 3
            medal = ''
            if i == 1:
                medal = '🥇 '
            elif i == 2:
                medal = '🥈 '
            elif i == 3:
                medal = '🥉 '
            
            candidate_name = candidate.user.get_full_name() or candidate.user.username
            
            self.stdout.write(
                f'   {medal}{i}. {candidate_name}'
            )
            self.stdout.write(
                f'      Party: {party}'
            )
            self.stdout.write(
                f'      Votes: {votes} ({percentage}%)'
            )
            self.stdout.write('')
        
        # Show winner
        if results_data['results']:
            winner = results_data['results'][0]
            winner_name = winner['candidate'].user.get_full_name() or winner['candidate'].user.username
            if winner['votes'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'   🏆 WINNER: {winner_name} with {winner["votes"]} votes ({winner["percentage"]}%)')
                )
        
        self.stdout.write('')