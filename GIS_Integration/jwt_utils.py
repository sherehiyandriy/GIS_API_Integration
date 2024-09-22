import os
import logging
from boxsdk import JWTAuth, Client

logger = logging.getLogger(__name__)

def get_jwt_access_token(auth):
    """Get the access token for the JWT assertion"""
    return auth.authenticate_instance()

def is_jwt_record_valid(auth):
    """Check if the JWT record is valid"""
    try:
        access_token = get_jwt_access_token(auth)
        return access_token is not None
    except Exception as e:
        logger.error(f"Invalid JWT record: {e}")
        return False

def store_access_token(auth):
    """Store the access tokens for the JWT app user"""
    try:
        access_token = get_jwt_access_token(auth)
        # You can store the access token in a secure store or environment variable
        os.environ['BOX_ACCESS_TOKEN'] = access_token
        logger.info("Access token stored securely.")
    except Exception as e:
        logger.error(f"Error storing access token: {e}")

def get_jwt_auth(box_config_file):
    """Get the auth for the JWT app user"""
    auth = JWTAuth.from_settings_file(box_config_file)
    return auth

def get_jwt_client(box_config_file):
    """Get the client for the JWT app user"""
    auth = get_jwt_auth(box_config_file)
    client = Client(auth)
    return client
