from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Rating, RatingType
from ppgc_backend.app.controllers.hotels.models import Hotel, Room
from ppgc_backend.app.controllers.properties.models import Property
from ppgc_backend.app.controllers.ratings.utils import AggregateRatingAClass
from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from ppgc_backend.log_config.logger_config import log_message

# Mapping of asset types to their models
ASSET_TYPE_MAP = {
    'hotel': Hotel,
    'room': Room,
    'property': Property,
}

# Mapping of asset types to RatingType enum
RATING_TYPE_MAP = {
    'hotel': RatingType.HOTEL,
    'room': RatingType.ROOM,
    'property': RatingType.PROPERTY,
}


async def get_asset_model(asset_type: str, db: AsyncSession) -> tuple:
    """Get the model class and column for the given asset type"""
    if asset_type not in ASSET_TYPE_MAP:
        raise ValueError(f"Invalid asset_type: {asset_type}")
    return ASSET_TYPE_MAP[asset_type], RATING_TYPE_MAP[asset_type]


async def rate_asset(
    data: dict,
    db: AsyncSession,
    commenter_id: int,
):
    """Rate a Hotel, Room, or Property.
    
    Args:
        data: dict with keys: asset_type, asset_id, comment, score
        db: AsyncSession
        commenter_id: ID of the user submitting the rating
    """
    asset_type = data.get('asset_type', '').lower()
    asset_id = data.get('asset_id')
    comment = data.get('comment')
    score = data.get('score', 5)

    # Validate inputs
    if not asset_type or asset_type not in ASSET_TYPE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset_type. Must be one of: {', '.join(ASSET_TYPE_MAP.keys())}"
        )

    if not asset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="asset_id is required"
        )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="comment is required"
        )

    if not isinstance(score, int) or score < 1 or score > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="score must be an integer between 1 and 5"
        )

    # Get the model class
    AssetModel, rating_type = await get_asset_model(asset_type, db)

    # Fetch the asset
    result = await db.execute(
        select(AssetModel).where(AssetModel.id == asset_id)
    )
    asset = result.scalars().first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{asset_type.capitalize()} with id {asset_id} not found"
        )

    try:
        # Create the rating instance with polymorphic fields
        rating_data = {
            'comment': comment,
            'score': score,
            'commenter_id': commenter_id,
            'rateable_type': rating_type,
            'rateable_id': asset_id,
        }

        # Set the specific relationship based on asset type
        if asset_type == 'hotel':
            rating_data['hotel_id'] = asset_id
        elif asset_type == 'room':
            rating_data['room_id'] = asset_id
        elif asset_type == 'property':
            rating_data['property_id'] = asset_id

        rating = Rating(**rating_data)
        db.add(rating)

        # Update the asset rating attributes (if it uses AggregateRatingAClass)
        if hasattr(asset, 'total_ratings'):
            asset.total_ratings += 1
        if hasattr(asset, 'total_stars'):
            asset.total_stars += score
        
        db.add(asset)
        await db.commit()
        await db.refresh(rating)

        if DEBUG:
            logger.info(f'**Successful rating of {asset_type} with id {asset_id}')

        return rating

    except Exception as e:
        await db.rollback()
        msg = f'**An error occurred rating {asset_type} with id {asset_id}. Reason: {e}'
        if DEBUG:
            logger.error(msg, exc_info=True)
        log_message('error', msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'An error occurred rating {asset_type}.'
        )


async def get_asset_ratings(
    asset_type: str,
    asset_id: int,
    db: AsyncSession,
    limit: int = 10,
    offset: int = 0,
):
    """Get all ratings for a specific asset"""
    if asset_type not in ASSET_TYPE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset_type. Must be one of: {', '.join(ASSET_TYPE_MAP.keys())}"
        )

    # Verify the asset exists
    AssetModel, rating_type = await get_asset_model(asset_type, db)
    asset_result = await db.execute(
        select(AssetModel).where(AssetModel.id == asset_id)
    )
    asset = asset_result.scalars().first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{asset_type.capitalize()} with id {asset_id} not found"
        )

    # Fetch ratings
    result = await db.execute(
        select(Rating)
        .where(
            Rating.rateable_type == rating_type,
            Rating.rateable_id == asset_id
        )
        .order_by(Rating.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    ratings = result.scalars().all()

    # Calculate average score
    if ratings:
        average_score = sum(r.score for r in ratings) / len(ratings)
    else:
        average_score = 0.0

    return {
        'total': len(ratings),
        'average_score': average_score,
        'ratings': ratings
    }


async def delete_rating(
    rating_id: int,
    db: AsyncSession,
    commenter_id: int,
):
    """Delete a rating (only the commenter can delete their own rating)"""
    result = await db.execute(
        select(Rating).where(Rating.id == rating_id)
    )
    rating = result.scalars().first()

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    if rating.commenter_id != commenter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own ratings"
        )

    try:
        # Decrement asset rating count
        asset_type = rating.rateable_type.value if hasattr(rating.rateable_type, 'value') else str(rating.rateable_type)
        AssetModel, _ = await get_asset_model(asset_type, db)

        asset_result = await db.execute(
            select(AssetModel).where(AssetModel.id == rating.rateable_id)
        )
        asset = asset_result.scalars().first()

        if asset:
            if hasattr(asset, 'total_ratings') and asset.total_ratings > 0:
                asset.total_ratings -= 1
            if hasattr(asset, 'total_stars'):
                asset.total_stars -= rating.score
            db.add(asset)

        await db.delete(rating)
        await db.commit()

        if DEBUG:
            logger.info(f'**Successfully deleted rating {rating_id}')

    except Exception as e:
        await db.rollback()
        msg = f'**An error occurred deleting rating {rating_id}. Reason: {e}'
        if DEBUG:
            logger.error(msg, exc_info=True)
        log_message('error', msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An error occurred deleting the rating.'
        )