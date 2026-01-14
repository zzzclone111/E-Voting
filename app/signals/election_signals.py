from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models import Election
from app.encryption import Encryption

@receiver(post_save, sender=Election)
def generate_election_keys(sender, instance, created, **kwargs):
    if created:  # Only run on creation
        encryption = Encryption()
        public_key = encryption.paillier.keys['public_key']
        private_key = encryption.paillier.keys['private_key']
        
        # Update the instance without triggering the save signal again
        Election.objects.filter(uuid=instance.uuid).update(
            public_key=public_key,
            private_key=private_key
        )