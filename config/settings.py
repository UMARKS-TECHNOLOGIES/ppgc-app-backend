import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key for cryptographic operations
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')

# Allowed hosts for the application
DEV_ENV_HOSTNAME=os.getenv('DEV_ENV_HOSTNAME')

# Debug mode
DEBUG = socket.gethostname() == DEV_ENV_HOSTNAME

# Allowed hosts for the application
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# SQLAlchemy database configuration for PostgreSQL
DEV_DATABASE_URL = os.getenv('DEV_DATABASE_URL')
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')
PROD_DATABASE_URL = os.getenv('PROD_DATABASE_URL')


EMAIL_VERIFICATION_CODE_TTL = int(os.getenv('EMAIL_VERIFICATION_CODE_TTL'))
TEST_EMAIL_VERIFICATION_CODE_TTL = int(os.getenv('TEST_EMAIL_VERIFICATION_CODE_TTL'))
TRANSIENT_EMAIL_VERIFICATION_TTL = int(os.getenv('TRANSIENT_EMAIL_VERIFICATION_TTL'))
TEST_TRANSIENT_EMAIL_VERIFICATION_TTL = int(os.getenv('TEST_TRANSIENT_EMAIL_VERIFICATION_TTL'))
TRANSIENT_EMAIL_INTERVAL = int(os.getenv('TRANSIENT_EMAIL_INTERVAL'))
TEST_TRANSIENT_EMAIL_INTERVAL = int(os.getenv('TEST_TRANSIENT_EMAIL_INTERVAL'))


# CORS settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = int(os.getenv('JWT_EXPIRATION_DELTA', 30))
