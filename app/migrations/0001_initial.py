import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.FileField(upload_to='uploads/')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Party',
                'verbose_name_plural': 'Parties',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('description', models.TextField()),
                ('private_key', models.CharField(default='', editable=False, max_length=500)),
                ('public_key', models.CharField(default='', editable=False, max_length=500)),
                ('is_public', models.BooleanField(default=False, help_text='If True, any registered user can vote. If False, only invited users can vote.')),
                ('active', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, help_text='When the election was activated', null=True)),
                ('closed_at', models.DateTimeField(blank=True, help_text='When the election was closed', null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_elections', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Election',
                'verbose_name_plural': 'Elections',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('profile', models.TextField(blank=True, help_text="User's background and qualifications")),
                ('manifesto', models.TextField(blank=True, help_text="User's policy positions and campaign promises")),
                ('avatar', models.ImageField(blank=True, help_text='Profile picture', null=True, upload_to='avatars/')),
                ('date_of_birth', models.DateField(blank=True, help_text='Date of birth', null=True)),
                ('location', models.CharField(blank=True, help_text='City, State/Province, Country', max_length=200)),
                ('gender', models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other'), ('N', 'Prefer not to say')], help_text='Gender identity', max_length=1)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profile',
                'verbose_name_plural': 'Profiles',
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('invited_email', models.EmailField(blank=True, help_text='Email address of the person being invited (optional for one-time links)', max_length=254, null=True)),
                ('is_one_time_link', models.BooleanField(default=False, help_text='If True, this is a one-time anonymous link that can be used by anyone')),
                ('invitation_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('message', models.TextField(blank=True, help_text='Optional personal message with the invitation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(help_text='When this invitation expires')),
                ('election', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='app.election')),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('invited_user', models.ForeignKey(blank=True, help_text='User being invited (if they have an account)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='election_invitations', to=settings.AUTH_USER_MODEL)),
                ('used_by', models.ForeignKey(blank=True, help_text='User who used this one-time link', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invitations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Election Invitation',
                'verbose_name_plural': 'Election Invitations',
                'ordering': ['-created_at'],
                'unique_together': {('election', 'invited_email')},
            },
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('symbol', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('election', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='candidates', to='app.election')),
                ('party', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='app.party')),
            ],
            options={
                'verbose_name': 'Candidate',
                'verbose_name_plural': 'Candidates',
                'ordering': ['election', 'user__last_name', 'user__first_name'],
                'unique_together': {('user', 'election')},
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('ballot', models.CharField(default='', editable=False, max_length=5000)),
                ('hashed', models.CharField(default='', editable=False, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('election', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='votes', to='app.election')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
                'ordering': ['-created'],
                'unique_together': {('user', 'election')},
            },
        ),
    ]
