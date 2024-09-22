import hmac
import hashlib
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def check_signature(secret, payload, signature):
    """Check the signature of the webhook request"""
    computed_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

def classify_file(file_id, classification_label, client):
    """Classify a file"""
    try:
        file = client.file(file_id).get()
        file.metadata().create({"Classification": classification_label})
        logger.info(f"File {file_id} classified as {classification_label}")
    except Exception as e:
        logger.error(f"Error classifying file: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify file")
