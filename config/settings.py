import os
import socket
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)\

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key for cryptographic operations
ACCESS_SECRET_KEY = os.getenv('ACCESS_SECRET_KEY', 'your_secret_key')

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

REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY')
REFRESH_TOKEN_EXPIRY_MINUTES=43200 # 30 days in minutes

# Remita / external payment gateway configuration
REMITA_BASE_URL = os.getenv('REMITA_BASE_URL', 'https://remitademo.net')
REMITA_API_KEY = os.getenv('REMITA_API_KEY')
REMITA_MERCHANT_ID = os.getenv('REMITA_MERCHANT_ID')
REMITA_SERVICE_TYPE_ID = os.getenv('REMITA_SERVICE_TYPE_ID')
# Optional override endpoints (paths appended to REMITA_BASE_URL)
REMITA_RRR_PATH = os.getenv('REMITA_RRR_PATH', '/remita/exapp/api/v1/send/api/echannel/rrr')
REMITA_VERIFY_PATH = os.getenv('REMITA_VERIFY_PATH', '/remita/exapp/api/v1/get/api/transaction/verify')
# Whether to include an Authorization: Bearer <API_KEY> header. If false, client will send API key in payload.
REMITA_USE_BEARER = os.getenv('REMITA_USE_BEARER', 'true').lower() in ('1','true','yes')