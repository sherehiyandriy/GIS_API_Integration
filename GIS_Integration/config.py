import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    box_config_file: str = os.getenv('BOX_CONFIG_FILE')
    ags_service_url: str = os.getenv('AGS_SERVICE_URL')
    fernet_key: str = os.getenv('FERNET_KEY')
    box_webhook_secret: str = os.getenv('BOX_WEBHOOK_SECRET')  # Added for webhook secret

    class Config:
        env_file = '.env'

settings = Settings()

# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # This logs to the console
        logging.FileHandler('app.log')  # This logs to a file named app.log
    ]
)
logger = logging.getLogger(__name__)
