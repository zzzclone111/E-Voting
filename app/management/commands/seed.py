from django.core.management.base import BaseCommand
from app.models import Election, Party, Candidate, Profile, Vote, Invitation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group, Permission
from app.encryption import Encryption
from datetime import datetime, timezone, timedelta
import random
from faker import Faker
import requests
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import time


class Command(BaseCommand):
    help = "Sets up comprehensive demo data with multiple elections, candidates, and users using realistic fake data"

    def fetch_random_face(self, gender=None, age_group=None, max_retries=2):
        """
        Fetch a random face from multiple sources with fallbacks
        
        Args:
            gender: 'male', 'female', or None for random
            age_group: 'young-adult', 'adult', 'elderly', or None for random
            max_retries: Maximum number of retry attempts
            
        Returns:
            ContentFile with image data or None if failed
        """
        # List of API endpoints to try (with fallbacks)
        endpoints = [
            # Fallback 1: Picsum with people photos (300x300) - more reliable
            "https://picsum.photos/300/300",
            # Fallback 2: Random user avatar generator
            "https://api.dicebear.com/7.x/avataaars/png",
            # Fallback 3: UI Avatars (generates initials-based avatars)
            f"https://ui-avatars.com/api/?size=300&background=random&name={'User'+str(random.randint(1,999))}",
        ]
        
        for endpoint_idx, endpoint in enumerate(endpoints):
            try:
                # Add cache busting parameter
                params = {'seed': random.randint(1, 100000)}
                
                # Make request with shorter timeout and proper headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(endpoint, params=params, headers=headers, timeout=8)
                response.raise_for_status()
                
                # Check if we got an image and it's not too small
                content_type = response.headers.get('content-type', '')
                if content_type.startswith('image/') and len(response.content) > 500:
                    # Generate unique filename
                    timestamp = int(time.time() * 1000)
                    filename = f"candidate_face_{timestamp}_{random.randint(1000, 9999)}.jpg"
                    
                    # Return ContentFile
                    return ContentFile(response.content, name=filename)
                    
            except (requests.exceptions.RequestException, KeyboardInterrupt) as e:
                # For keyboard interrupt, re-raise to allow user to stop
                if isinstance(e, KeyboardInterrupt):
                    raise
                # For network errors, just continue to next endpoint
                continue
                
        # If all endpoints fail, return None silently
        return None

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data from the database before seeding',
        )

    def clear_all_data(self):
        """Clear all data from the database in the correct order to handle foreign key constraints"""
        self.stdout.write(self.style.WARNING("🗑️  Clearing all existing data..."))
        
        try:
            # Clear in reverse dependency order to avoid foreign key constraint violations
            self.stdout.write("   - Clearing votes...")
            Vote.objects.all().delete()
            
            self.stdout.write("   - Clearing invitations...")
            Invitation.objects.all().delete()
            
            self.stdout.write("   - Clearing candidates...")
            Candidate.objects.all().delete()
            
            self.stdout.write("   - Clearing profiles...")
            Profile.objects.all().delete()
            
            self.stdout.write("   - Clearing elections...")
            Election.objects.all().delete()
            
            self.stdout.write("   - Clearing parties...")
            Party.objects.all().delete()
            
            self.stdout.write("   - Clearing non-superuser users...")
            User.objects.filter(is_superuser=False).delete()
            
            self.stdout.write("   - Clearing groups...")
            Group.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS("✅ All data cleared successfully"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error clearing data: {e}"))
            raise

    def _choose_candidate_with_preference(self, candidates):
        """Choose a candidate with some realistic voting preferences"""
        if not candidates:
            return None
        
        # Create weights based on party affiliation and randomness
        weights = []
        for candidate in candidates:
            weight = 1.0  # Base weight
            
            # Popular parties get slight boost
            if candidate.party:
                popular_parties = ["Progressive Alliance", "Conservative Coalition", "Liberal Democrats"]
                if candidate.party.name in popular_parties:
                    weight *= 1.5
                    
            # Add some randomness
            weight *= random.uniform(0.5, 2.0)
            weights.append(weight)
        
        # Choose candidate based on weights
        return random.choices(candidates, weights=weights, k=1)[0]

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.clear_all_data()
        else:
            self.stdout.write(self.style.WARNING("Use --clear flag to clear existing data before seeding"))
            self.stdout.write(self.style.WARNING("Proceeding without clearing existing data..."))

        try:
            # Create groups and assign permissions
            self.stdout.write(self.style.SUCCESS("Creating user groups..."))
            officials_group, _ = Group.objects.get_or_create(name="Officials")
            candidates_group, _ = Group.objects.get_or_create(name="Candidates")
            citizens_group, _ = Group.objects.get_or_create(name="Citizens")
            
            # Assign permissions to groups
            content_types = ContentType.objects.filter(app_label="app")
            permissions = Permission.objects.filter(content_type__in=content_types)
            officials_group.permissions.set(permissions)
            
            self.stdout.write(self.style.SUCCESS("✅ Created user groups with permissions"))

            # Create admin user if doesn't exist
            admin, created = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@intikhab.org",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "is_superuser": True,
                    "is_staff": True
                }
            )
            if created:
                admin.set_password("admin123")
                admin.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Created admin user: {admin.username}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Admin user already exists: {admin.username}"))

            # Create diverse political parties
            self.stdout.write(self.style.SUCCESS("Creating political parties..."))
            parties_data = [
                {"name": "Progressive Alliance", "description": "Forward-thinking policies for sustainable development"},
                {"name": "Conservative Coalition", "description": "Traditional values and fiscal responsibility"},
                {"name": "Green Movement", "description": "Environmental protection and renewable energy"},
                {"name": "Labor Unity Party", "description": "Workers' rights and social justice"},
                {"name": "Liberal Democrats", "description": "Individual freedoms and democratic reforms"},
                {"name": "National Security Party", "description": "Strong defense and border security"},
                {"name": "Tech Innovation Party", "description": "Digital transformation and innovation"},
                {"name": "Rural Development Party", "description": "Agricultural and rural community focus"},
            ]
            
            parties = []
            for party_data in parties_data:
                party = Party.objects.create(
                    name=party_data["name"],
                    symbol=f"uploads/{fake.file_name(extension='jpg')}"
                )
                parties.append(party)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(parties)} political parties"))

            # Create many users with realistic data
            self.stdout.write(self.style.SUCCESS("Creating users with realistic data..."))
            
            # Create officials (5-8 users)
            officials = []
            for i in range(random.randint(5, 8)):
                username = f"official_{fake.random_int(1000, 9999)}_{i+1}"
                official = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    password="password123",
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                official.groups.add(officials_group)
                officials.append(official)
            
            # Create potential candidates (20-30 users)
            candidate_users = []
            for i in range(random.randint(20, 30)):
                username = f"candidate_{fake.random_int(1000, 9999)}_{i+1}"
                candidate = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    password="password123",
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                candidate.groups.add(candidates_group)
                candidate_users.append(candidate)
                
                # Create profile for each candidate
                gender_choice = random.choice(['M', 'F', 'O'])
                profile = Profile.objects.create(
                    user=candidate,
                    profile=fake.text(max_nb_chars=300),
                    manifesto=fake.text(max_nb_chars=500),
                    location=f"{fake.city()}, {fake.state_abbr()}",
                    gender=gender_choice
                )
                
                # Fetch and assign a realistic face based on gender (optional, non-blocking)
                try:
                    # Map profile gender to API gender
                    api_gender = None
                    if gender_choice == 'M':
                        api_gender = 'male'
                    elif gender_choice == 'F':
                        api_gender = 'female'
                    # For 'O' (Other), we'll use random (None)
                    
                    face_image = self.fetch_random_face(gender=api_gender)
                    if face_image:
                        profile.avatar.save(face_image.name, face_image, save=True)
                        self.stdout.write(f"   ✅ Assigned face to {candidate.get_full_name()}")
                    else:
                        self.stdout.write(f"   ⚠️  No face assigned to {candidate.get_full_name()}")
                        
                except KeyboardInterrupt:
                    # Re-raise keyboard interrupt so user can stop the process
                    raise
                except Exception as e:
                    self.stdout.write(f"   ❌ Error assigning face to {candidate.get_full_name()}: {str(e)[:100]}")
                    # Continue without face - it's not critical
            
            # Create regular citizens (15-25 users)
            citizens = []
            for i in range(random.randint(15, 25)):
                username = f"citizen_{fake.random_int(1000, 9999)}_{i+1}"
                citizen = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    password="password123",
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                citizen.groups.add(citizens_group)
                citizens.append(citizen)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(officials)} officials, {len(candidate_users)} candidates, {len(citizens)} citizens"))

            # Create diverse elections with varying dates
            self.stdout.write(self.style.SUCCESS("Creating elections with varying timeframes..."))
            
            now = datetime.now(timezone.utc)
            elections = []
            
            # Election templates with realistic data
            election_templates = [
                {
                    "name": "Presidential Election 2025",
                    "description": "National presidential election to elect the next president for a four-year term.",
                    "type": "completed"
                },
                {
                    "name": "Congressional Midterm Elections",
                    "description": "Election for House of Representatives and Senate seats in various districts.",
                    "type": "ongoing"
                },
                {
                    "name": "State Governor Election",
                    "description": "Gubernatorial election to choose the state's chief executive officer.",
                    "type": "upcoming"
                },
                {
                    "name": "Municipal Mayor Election",
                    "description": "Local election for city mayor and municipal council positions.",
                    "type": "completed"
                },
                {
                    "name": "School Board Elections",
                    "description": "Educational district elections for school board member positions.",
                    "type": "ongoing"
                },
                {
                    "name": "County Commissioner Race",
                    "description": "County-level election for commissioner positions and local measures.",
                    "type": "upcoming"
                },
                {
                    "name": "Special Senate Election",
                    "description": "Special election to fill vacant Senate seat following resignation.",
                    "type": "completed"
                },
                {
                    "name": "Judicial Elections",
                    "description": "Non-partisan election for local and state judicial positions.",
                    "type": "upcoming"
                },
                {
                    "name": "Ballot Measures Referendum",
                    "description": "Referendum on various local and state ballot measures and propositions.",
                    "type": "ongoing"
                }
            ]
            
            for template in election_templates:
                # Generate encryption keys for each election
                encryption = Encryption()
                public_key = str(encryption.paillier.keys['public_key'])
                private_key = str(encryption.paillier.keys['private_key'])
                
                # Set dates based on election type
                if template["type"] == "completed":
                    # Elections that ended 1-90 days ago
                    end_date = now - timedelta(days=random.randint(1, 90))
                    start_date = end_date - timedelta(days=random.randint(7, 30))
                    active = False
                elif template["type"] == "ongoing":
                    # Elections that started 1-7 days ago and end 1-14 days from now
                    start_date = now - timedelta(days=random.randint(1, 7))
                    end_date = now + timedelta(days=random.randint(1, 14))
                    active = True
                else:  # upcoming
                    # Elections that start 1-60 days from now
                    start_date = now + timedelta(days=random.randint(1, 60))
                    end_date = start_date + timedelta(days=random.randint(7, 30))
                    active = False
                
                election = Election.objects.create(
                    name=template["name"],
                    description=template["description"],
                    start_date=start_date,
                    end_date=end_date,
                    created_by=random.choice(officials),
                    public_key=public_key,
                    private_key=private_key,
                    active=active
                )
                elections.append(election)
                
                # Add candidates to each election (2-6 candidates per election)
                num_candidates = random.randint(2, 6)
                selected_candidates = random.sample(candidate_users, min(num_candidates, len(candidate_users)))
                
                for i, candidate_user in enumerate(selected_candidates):
                    # Some candidates have party affiliation, some are independent
                    party = random.choice(parties) if random.random() > 0.3 else None
                    
                    Candidate.objects.create(
                        user=candidate_user,
                        party=party,
                        election=election,
                        symbol=f"uploads/{fake.file_name(extension='jpg')}" if random.random() > 0.5 else None
                    )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(elections)} elections with candidates"))
            
            # Cast votes for completed and ongoing elections
            self.stdout.write(self.style.SUCCESS("Casting votes for completed and ongoing elections..."))
            total_votes_cast = 0
            
            # Get all voters (citizens, officials, and some candidates who aren't running in specific elections)
            all_voters = list(citizens) + list(officials)
            
            for election in elections:
                # Only cast votes for completed and ongoing elections
                if election.end_date < now or (election.start_date <= now <= election.end_date):
                    candidates_in_election = list(election.candidates.all())
                    
                    if not candidates_in_election:
                        continue
                    
                    # Add non-candidate users to voters for this election
                    candidate_users_in_election = [c.user for c in candidates_in_election]
                    available_voters = [v for v in all_voters if v not in candidate_users_in_election]
                    
                    # Cast votes for 30-80% of available voters
                    num_voters = random.randint(
                        int(len(available_voters) * 0.3), 
                        min(len(available_voters), int(len(available_voters) * 0.8))
                    )
                    
                    selected_voters = random.sample(available_voters, num_voters)
                    
                    for voter in selected_voters:
                        # Each voter picks a candidate (with some preference for popular parties)
                        candidate = self._choose_candidate_with_preference(candidates_in_election)
                        
                        try:
                            # Create the vote using proper encryption
                            vote = Vote(
                                user=voter,
                                election=election
                            )
                            vote._candidate = candidate  # Temporary attribute for encryption
                            vote.save()
                            total_votes_cast += 1
                            
                        except Exception as e:
                            # Skip if vote already exists or other error
                            continue
            
            self.stdout.write(self.style.SUCCESS(f"✅ Cast {total_votes_cast} votes across elections"))
            
            # Summary
            completed_elections = len([e for e in elections if e.end_date < now])
            ongoing_elections = len([e for e in elections if e.start_date <= now <= e.end_date])
            upcoming_elections = len([e for e in elections if e.start_date > now])
            
            self.stdout.write(self.style.SUCCESS("=" * 50))
            self.stdout.write(self.style.SUCCESS("🗳️  SEED DATA SUMMARY"))
            self.stdout.write(self.style.SUCCESS("=" * 50))
            self.stdout.write(self.style.SUCCESS(f"👥 Users: {User.objects.count()} total"))
            self.stdout.write(self.style.SUCCESS("   - Admins: 1"))
            self.stdout.write(self.style.SUCCESS(f"   - Officials: {len(officials)}"))
            self.stdout.write(self.style.SUCCESS(f"   - Candidates: {len(candidate_users)}"))
            self.stdout.write(self.style.SUCCESS(f"   - Citizens: {len(citizens)}"))
            self.stdout.write(self.style.SUCCESS(f"🏛️  Parties: {len(parties)}"))
            self.stdout.write(self.style.SUCCESS(f"🗳️  Elections: {len(elections)} total"))
            self.stdout.write(self.style.SUCCESS(f"   - Completed: {completed_elections}"))
            self.stdout.write(self.style.SUCCESS(f"   - Ongoing: {ongoing_elections}"))
            self.stdout.write(self.style.SUCCESS(f"   - Upcoming: {upcoming_elections}"))
            self.stdout.write(self.style.SUCCESS(f"🏃 Candidates: {Candidate.objects.count()} total"))
            self.stdout.write(self.style.SUCCESS(f"🗳️  Votes Cast: {Vote.objects.count()} total"))
            self.stdout.write(self.style.SUCCESS("=" * 50))
            self.stdout.write(self.style.SUCCESS("Login credentials:"))
            self.stdout.write(self.style.SUCCESS("  Admin: admin / admin123"))
            self.stdout.write(self.style.SUCCESS(f"  Officials: {officials[0].username} / password123"))
            self.stdout.write(self.style.SUCCESS(f"  Candidates: {candidate_users[0].username} / password123"))
            self.stdout.write(self.style.SUCCESS(f"  Citizens: {citizens[0].username} / password123"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating seed data: {e}"))