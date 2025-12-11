import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key for cryptographic operations
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_secret_key')

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


EMAIL_VERIFICATION_CODE_TTL=300
TEST_EMAIL_VERIFICATION_CODE_TTL=60 
TRANSIENT_EMAIL_VERIFICATION_TTL=1800
TEST_TRANSIENT_EMAIL_VERIFICATION_TTL=60 
TRANSIENT_CLEANUP_INTERVAL=60
TEST_TRANSIENT_CLEANUP_INTERVAL=10


# CORS settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# JWT settings
JWT_EXPIRATION_DELTA=1440
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = int(os.getenv('JWT_EXPIRATION_DELTA', 30))

PASSWORD_RESET_TTL = 1800 # 30 minutes
TEST_PASSWORD_RESET_TTL = 10 # 10 SES

SUPER_ADMIN_EMAIL_ADDRESS = os.getenv('SUPER_ADMIN_EMAIL_ADDRESS')
SUPER_ADMIN_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')

REAL_TEST_EMAIL = os.getenv('REAL_TEST_EMAIL')