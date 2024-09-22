import os
import logging
import json
from fastapi import FastAPI, Request, HTTPException
from boxsdk import JWTAuth, Client
from dotenv import load_dotenv
from pyproj import Transformer
import httpx
from crypto_utils import encrypt_token, decrypt_token, refresh_token  # Import the functions
from jwt_utils import get_jwt_auth, get_jwt_client  # Import JWT utilities
from utils import check_signature, classify_file  # Import utility functions

load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # This logs to the console
        logging.FileHandler('app.log')  # This logs to a file named app.log
    ]
)
logger = logging.getLogger(__name__)

# Box API configuration
BOX_CONFIG_FILE = os.getenv('BOX_CONFIG_FILE')

# Initialize Box client with JWT authentication
auth = get_jwt_auth(BOX_CONFIG_FILE)
client = get_jwt_client(BOX_CONFIG_FILE)

# Coordinate converter from 4326 to 3857 used by ArcGIS Online
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")

# ArcGIS service URL from environment variable
AGS_SERVICE_URL = os.getenv('AGS_SERVICE_URL')

# Fernet key for encryption/decryption from environment variable
FERNET_KEY = os.getenv('FERNET_KEY')

# Webhook secret from environment variable
WEBHOOK_SECRET = os.getenv('BOX_WEBHOOK_SECRET')

def check_file_exists(file_id):
    try:
        file_info = client.file(file_id).get()
        logger.info(f"File exists: {file_info}")
        return True
    except Exception as e:
        logger.error(f"Error checking file existence: {e}")
        return False

def get_metadata(file_id):
    try:
        # Fetch the file information with the specific metadata fields
        file_info = client.file(file_id=file_id).get(fields=['id', 'type', 'name', 'metadata.global.boxCaptureV1'])
        
        # Extract the metadata from the response
        metadata = file_info['metadata']['global']['boxCaptureV1']
        
        logger.info(f"Got metadata instance: {metadata}")
        return metadata
    except KeyError as e:
        logger.error(f"Error fetching metadata: {e} - Key not found in the response.")
        return None
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        return None

async def add_feature_to_arcgis(x, y, attributes):
    try:
        features = [{
            "geometry": {"x": x, "y": y},
            "attributes": attributes
        }]
        data = {
            "features": json.dumps(features),
            "f": "json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AGS_SERVICE_URL}/addFeatures", data=data)
            response.raise_for_status()
            logger.info(f"ArcGIS add features response: {response.status_code} - {response.text}")
            return response.json()
    except Exception as e:
        logger.error(f"Error adding feature to ArcGIS: {e}")
        return None

async def delete_feature_from_arcgis(box_file_id):
    try:
        data = {
            "where": f"BoxFileID='{box_file_id}'",
            "f": "json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{AGS_SERVICE_URL}/deleteFeatures", data=data)
            response.raise_for_status()
            logger.info(f"ArcGIS delete features response: {response.status_code} - {response.text}")
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting feature from ArcGIS: {e}")
        return None

@app.post("/webhook/box")
async def handle_box_webhook(request: Request):
    payload = await request.json()
    signature = request.headers.get('box-signature')
    logger.info(f"Received Payload: {payload}")
    
    try:
        # Check the signature of the webhook request
        check_signature(WEBHOOK_SECRET, await request.body(), signature)

        if payload.get('trigger') == 'FILE.UPLOADED':
            file_id = payload['source']['id']
            logger.info(f"Processing file ID: {file_id}")
            if check_file_exists(file_id):
                metadata = get_metadata(file_id)
                if metadata:
                    logger.info(f"Metadata: {metadata}")
                    
                    # Extract latitude and longitude
                    latitude, _, longitude, _ = metadata['location'].split(' ')
                    latitude = float(latitude)
                    longitude = float(longitude)
                    
                    # Convert to x, y coordinates
                    x, y = transformer.transform(latitude, -longitude)
                    
                    logger.info(f"Coordinates: x={x}, y={y}")
                    
                    # Encrypt file_id
                    encrypted_file_id = encrypt_token(file_id, FERNET_KEY)
                    
                    # Add feature to ArcGIS
                    attributes = {
                        "BoxFileID": encrypted_file_id,
                        "Latitude": latitude,
                        "Longitude": longitude
                    }
                    arcgis_response = await add_feature_to_arcgis(x, y, attributes)
                    
                    # Classify the file
                    classify_file(file_id, "Confidential", client)
                    
                    return {"x": x, "y": y, "arcgis_response": arcgis_response}
        
        elif payload.get('trigger') == 'FILE.TRASHED':
            file_id = payload['source']['id']
            logger.info(f"Processing file ID for deletion: {file_id}")
            
            # Encrypt file_id for deletion
            encrypted_file_id = encrypt_token(file_id, FERNET_KEY)
            
            arcgis_response = await delete_feature_from_arcgis(encrypted_file_id)
            return {"status": "success", "arcgis_response": arcgis_response}

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling webhook event: {e}")
        return {"status": "error", "message": "Failed to process webhook event"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
