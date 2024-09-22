# generate_fernet_key.py

from cryptography.fernet import Fernet

def generate_fernet_key():
    """Generate a new Fernet key."""
    key = Fernet.generate_key()
    print(f"Generated Fernet Key: {key.decode()}")

if __name__ == "__main__":
    generate_fernet_key()
