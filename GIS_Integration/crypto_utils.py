from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)

def encrypt_token(token: str, fernet_key: str) -> str:
    """Encrypt token."""
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()

def decrypt_token(token: str, fernet_key: str) -> str:
    """Decrypt token."""
    fernet = Fernet(fernet_key)
    try:
        decrypted = fernet.decrypt(token.encode())
        return decrypted.decode()
    except InvalidToken as e:
        logger.error(f"Invalid token: {e}")
        raise

def refresh_token(auth):
    """Refresh Box API token."""
    auth.authenticate_instance()  # Refreshes the access token
    logger.info(f"Token refreshed. New access token: {auth.access_token[:10]}...")  # Log a portion of the token for debugging
    return auth.access_token
