from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.database import get_db
from ppgc_backend.app.controllers.auth.services import decode_user_from_token
from ppgc_backend.app.models import User
from .schemas import RatingReviewSchema, RatingResponseSchema, RatingListSchema
from .services import rate_asset, get_asset_ratings, delete_rating

router = APIRouter(prefix='/ratings', tags=['ratings'])


@router.post(
    '',
    status_code=status.HTTP_201_CREATED,
    response_model=RatingResponseSchema,
    response_description="Rating created successfully"
)
async def create_rating(
    data: RatingReviewSchema,
    commenter: User = Depends(decode_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a rating for a Hotel, Room, or Property.
    
    - **asset_type**: One of 'hotel', 'room', or 'property'
    - **asset_id**: The ID of the asset to rate
    - **comment**: Review comment (required)
    - **score**: Rating score from 1 to 5
    """
    rating_data = {
        'asset_type': data.asset_type,
        'asset_id': data.asset_id,
        'comment': data.comment,
        'score': data.score,
    }

    rating = await rate_asset(rating_data, db, commenter.id)
    return RatingResponseSchema.from_orm_with_relations(rating)


@router.get(
    '/{asset_type}/{asset_id}',
    status_code=status.HTTP_200_OK,
    response_model=RatingListSchema,
    response_description="Ratings retrieved successfully"
)
async def get_ratings(
    asset_type: str,
    asset_id: int,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all ratings for a specific asset (Hotel, Room, or Property).
    
    - **asset_type**: One of 'hotel', 'room', or 'property'
    - **asset_id**: The ID of the asset
    - **limit**: Maximum number of ratings to return (default 10)
    - **offset**: Offset for pagination (default 0)
    """
    result = await get_asset_ratings(asset_type, asset_id, db, limit, offset)
    
    return RatingListSchema(
        total=result['total'],
        average_score=result['average_score'],
        ratings=[RatingResponseSchema.from_orm_with_relations(r) for r in result['ratings']]
    )


@router.delete(
    '/{rating_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Rating deleted successfully"
)
async def delete_user_rating(
    rating_id: int,
    commenter: User = Depends(decode_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a rating (only the commenter can delete their own rating).
    
    - **rating_id**: The ID of the rating to delete
    """
    await delete_rating(rating_id, db, commenter.id)
    return None
