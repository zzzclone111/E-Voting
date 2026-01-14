from django.contrib import messages
import json
from app.encryption import Encryption, Ciphertext

def start_election(self, request, queryset):
        for election in queryset:
            if election.active:
                self.message_user(
                    request,
                    f"Election '{election.name}' is already started",
                    messages.INFO
                )
                continue
            # We can have the key generation logic here if we want.
            election.active = True
            election.save()

            self.message_user(
                request,
                f"Successfully started election '{election.name}'",
                messages.SUCCESS
            ) 

def end_election(modeladmin, request, queryset):
    for election in queryset:
        if not election.active:
            modeladmin.message_user(
                request,
                f"Election '{election.name}' is already ended",
                messages.WARNING
            )
            continue
        try:
            votes = election.votes.all()
            if not votes.exists():
                modeladmin.message_user(
                    request,
                    f"No votes found for election '{election.name}'",
                    messages.WARNING
                )
                continue


            cleaned_key_pb = election.public_key.replace("'", '"')
            public_key = json.loads(cleaned_key_pb)

            cleaned_key_pv = election.private_key.replace("'", '"')
            private_key = json.loads(cleaned_key_pv)
            encryption = Encryption(public_key=f"{public_key['g']},{public_key['n']}", private_key=f"{private_key['phi']}")

            candidates_length = len(json.loads(votes[0].ballot))

            encrypted_positive_total = [0] * candidates_length #step1: obtained by homomorphic addition of votes
            encrypted_negative_total = [None] * candidates_length #step2: obtained by ecnrypted negative of result
            encrypted_zero_sum = [None] * candidates_length #step3: obtained by homomorphic addition of step1 and step2
            zero_randomness = [None] * candidates_length #step4: obtained by extracting randomness of zero vector using priv key
            
            # STEP 1 (homomorphic tallying)
            for i in range(len(votes)):
                ballot = json.loads(votes[i].ballot)
                for j in range(len(ballot)):
                    json_str_positive = json.dumps({'ciphertext': ballot[j], 'randomness': None})
                    ct_temp_positive = Ciphertext.from_json(json_str_positive)
                    if i == 0:
                        encrypted_positive_total[j] = ct_temp_positive    
                    else:
                        encrypted_positive_total[j] = encryption.add(encrypted_positive_total[j], ct_temp_positive)

            serialized_encrypted_total = [ct.to_json() for ct in encrypted_positive_total]
            election.encrypted_positive_total = json.dumps(serialized_encrypted_total)

            # STEP 2 (decryption)
            print("Decrypting total: \n")
            decrypted_positive_total = []
            for i in encrypted_positive_total:
                decrypted_positive_total.append(encryption.decrypt(i))
            print("Decrypted positive total: ", decrypted_positive_total)
            election.decrypted_total = json.dumps(decrypted_positive_total)

            decrypted_negative_total = [-x for x in decrypted_positive_total]
            for i in range(len(decrypted_negative_total)):
                encrypted_negative_total[i] = encryption.encrypt(decrypted_negative_total[i], 1) #encrypt with randomness 1
            serialized_encrypted_ng_total = [ct.to_json() for ct in encrypted_negative_total]
            election.encrypted_negative_total = json.dumps(serialized_encrypted_ng_total)

            # STEP 3 (obain zero sum vector)
            for i in range(len(encrypted_positive_total)):
                encrypted_zero_sum[i] = encryption.add(encrypted_positive_total[i], encrypted_negative_total[i])
            serialized_zero_sum = [ct.to_json() for ct in encrypted_zero_sum]
            election.encrypted_zero_sum = json.dumps(serialized_zero_sum)

            # STEP 4 (obtain randomness of zero vector)
            for i in range(len(encrypted_zero_sum)):
                zero_randomness[i] = encryption.extract_randomness_from_zero_vector(encrypted_zero_sum[i])
            election.zero_randomness = json.dumps(zero_randomness)
            
            # End the election
            election.active = False
            election.save()
            
            modeladmin.message_user(
                request,
                f"Successfully ended election '{election.name}'",
                messages.SUCCESS
            )
            
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error ending election '{election.name}': {str(e)}",
                messages.ERROR
            )

# Add a description for the admin interface
end_election.short_description = "End selected elections"
start_election.short_description = "Start selected elections"