from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64


def encrypt_with_public_key(plain_text):
    plain_bytes = plain_text.encode()

    with open("logging_library/keys/public_key.pem", "rb") as f:
        public_key_data = f.read()
        public_key = load_pem_public_key(public_key_data)

    encrypted = public_key.encrypt(
        plain_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return base64.b64encode(encrypted).decode()


# Example usage
if __name__ == "__main__":
    plaintext = "Admin2025"
    print("Original Plaintext: ", plaintext)
    encrypted_message = encrypt_with_public_key(plaintext)
    print("Encrypted Message: ", encrypted_message)
