from lightphe.cryptosystems.Paillier import Paillier
from sympy import mod_inverse
import hashlib
import json

class Ciphertext:
    def __init__(self, ciphertext: int, randomness: int = None):
        """
        Initialize a Ciphertext object.
        
        :param ciphertext: The encrypted value
        :param randomness: The randomness used in encryption (optional)
        """
        self.ciphertext = ciphertext
        self.randomness = randomness

    def __repr__(self):
        """
        Provide a string representation of the CipherData object for debugging.
        """
        return f"CipherData(ciphertext='{self.ciphertext}', randomness='{self.randomness}')"

    def to_json(self):
        """
        Convert the ciphertext object to JSON format.
        """
        return json.dumps({
            'ciphertext': str(self.ciphertext),
            'randomness': str(self.randomness) if self.randomness else None
        })

    @classmethod
    def from_json(cls, json_str):
        """
        Create a Ciphertext object from JSON string.
        """
        data = json.loads(json_str)
        return cls(int(data['ciphertext']), int(data['randomness']) if data['randomness'] else None)

class Encryption:
    def __init__(self, public_key: str = None, private_key: str = None):
        """
        Initialize the Encryption class with a public and private key.
        
        :param public_key: The public key as 'g,n' string
        :param private_key: The private key phi value
        """
        if public_key is None and private_key is None:
            self.paillier = Paillier()
        elif public_key is not None and private_key is None:
            public_key_g, public_key_n = map(int, public_key.split(','))
            keys = {"public_key": {"g": public_key_g, "n": public_key_n}}
            self.paillier = Paillier(keys)
        else:
            public_key_g, public_key_n = map(int, public_key.split(','))
            private_key = int(private_key)
            keys = {
                "public_key": {"g": public_key_g, "n": public_key_n},
                "private_key": {"phi": private_key}
            }
            self.paillier = Paillier(keys)
    
    def generate_random_key(self):
        """
        Generate a random key.
        """
        return self.paillier.generate_random_key()

    def encrypt(self, plaintext: int, rand: int = None) -> Ciphertext:
        """
        Encrypt the given plaintext.

        :param plaintext: The plaintext integer to be encrypted
        :param rand: Optional randomness value
        :return: Ciphertext object
        """
        if rand is None:
            rand = self.generate_random_key()
        ct = self.paillier.encrypt(plaintext, rand)
        return Ciphertext(ct, rand)

    def add(self, ct1: Ciphertext, ct2: Ciphertext) -> Ciphertext:
        """
        Homomorphically add two ciphertexts.

        :param ct1: First Ciphertext object
        :param ct2: Second Ciphertext object
        :return: Ciphertext object containing encrypted sum
        """
        sum_ct = self.paillier.add(ct1.ciphertext, ct2.ciphertext)
        combined_randomness = None
        if ct1.randomness and ct2.randomness:
            combined_randomness = (ct1.randomness * ct2.randomness) % self.paillier.ciphertext_modulo
        return Ciphertext(sum_ct, combined_randomness)
    
    def decrypt(self, ct: Ciphertext) -> int:
        """
        Decrypt the given ciphertext.

        :param ct: Ciphertext object to decrypt
        :return: Decrypted plaintext
        """
        return self.paillier.decrypt(ct.ciphertext)

    def verify_zero(self, ct: Ciphertext) -> bool:
        """
        Verify if a ciphertext encrypts zero without decryption.
        
        :param ct: Ciphertext object to verify
        :return: True if the ciphertext encrypts zero
        """
        if not hasattr(self.paillier, 'keys') or 'private_key' not in self.paillier.keys:
            raise ValueError("Private key required for zero verification")
            
        public_key_n = self.paillier.plaintext_modulo
        phi_n = self.paillier.keys["private_key"]["phi"]
        m = mod_inverse(public_key_n, phi_n)
        r = pow(ct.ciphertext, m, public_key_n)
        
        test_ct = self.encrypt(0, r)
        return test_ct.ciphertext == ct.ciphertext

    def hash(self, data: str) -> str:
        """
        Create a SHA-256 hash of the input data.

        :param data: String data to hash
        :return: Hexadecimal hash string
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def extract_randomness_from_zero_vector(self, ciphertext):
        """
        Return the randomness associated with a zero vector.

        :param data: Ciphertext object
        :return: Randomness integer
        """
        # Step 1: Compute M = N^(-1) mod phi(N)
        public_key_n = self.paillier.plaintext_modulo
        phi_n = self.paillier.keys["private_key"]["phi"]
        m = mod_inverse(public_key_n, phi_n)
        
        # Step 2: Compute r = c^M mod N
        r = pow(ciphertext.ciphertext, m, public_key_n)
        return r