# ==============================
# Set your Cloudinary credentials
# ==============================
from typing import Any
from dotenv import load_dotenv

# Import the Cloudinary libraries
# ==============================
import cloudinary
from cloudinary.uploader import upload
from cloudinary.uploader import destroy

load_dotenv()

from ppgc_backend.config.settings import (
    CLOUDINARY_API_KEY, 
    CLOUDINARY_API_SECRET,
)

cloudinary.config(
    cloud_name="dzar0gusv",  
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)

def upload_image(file: Any, public_id: str = None):
    response = upload(
        file,
        # public_id=public_id,
        resource_type="image",
        folder="image_uploads"
        # overwrite=True,
        # upload_preset="ml_default",  # or your preset
    )
    return response

def delete_image(public_id: str):
    return destroy(
        public_id,
        resource_type="image",
        invalidate=True,
    )
