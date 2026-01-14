from django.core.management.base import BaseCommand
from app.email_utils import test_email_configuration


class Command(BaseCommand):
    help = 'Test the SendGrid email configuration'

    def handle(self, *args, **options):
        self.stdout.write('Testing SendGrid email configuration...')
        
        success = test_email_configuration()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Email configuration test successful! Check your email.')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Email configuration test failed. Check your settings and logs.')
            )