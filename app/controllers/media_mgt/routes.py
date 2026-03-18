from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from .schemas import (
    DeleteRequest,
    DeleteResponse,
    UploadResponseItem,
)
from .utils import upload_image, cloudinary
from ppgc_backend.config.settings import logger, DEBUG

router = APIRouter(prefix="/media", tags=["Media"])

@router.post("/upload/", response_model=List[UploadResponseItem])
async def handle_image_upload(files: List[UploadFile] = File(...)):
    """
    Upload multiple images to Cloudinary
    """
    results = []

    try:
        for file in files:
            upload_result = upload_image(file.file)
            results.append(upload_result)

        return results

    except Exception as e:
        e_msg = f"Image upload failed: {str(e)}"
        if DEBUG:
            logger.info(e_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e_msg
        )
    

@router.delete("/delete/", response_model=DeleteResponse)
async def delete_images(payload: DeleteRequest):
    """
    Delete multiple images from Cloudinary using public_ids
    """
    try:
        result = cloudinary.api.delete_resources(payload.public_ids)

        return {"deleted": result.get("deleted", {})}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image deletion failed: {str(e)}"
        )