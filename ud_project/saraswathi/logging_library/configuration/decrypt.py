import sys
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
import cryptography.hazmat.backends.openssl.backend as backend


def decrypt(cipher_text):
    # print("Decrypting the password...")
    # print("cipher_text: ", cipher_text)
    encrypted_bytes = base64.b64decode(cipher_text)

    # Load the private key from file

    # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # # Path to run decrypt.py locally for testing
    # with open("../keys/private_key.pem", "rb") as f:
    #     private_key_data = f.read()
    #     private_key = serialization.load_pem_private_key(
    #         private_key_data, password=None, backend=backend
    #     )
    # # - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    with open("logging_library/keys/private_key.pem", "rb") as f:
        private_key_data = f.read()
        private_key = serialization.load_pem_private_key(
            private_key_data, password=None, backend=backend
        )

    # Decrypt using the private key
    decrypted = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return decrypted.decode()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decrypt.py <cipher_text>")
        sys.exit(1)

    cipher_text = sys.argv[1]
    try:
        print("Decrypted text: ", decrypt(cipher_text))
    except Exception as e:
        print("Error occurred during decryption:", e)
