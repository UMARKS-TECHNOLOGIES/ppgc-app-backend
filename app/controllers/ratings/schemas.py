from typing import Optional, Literal
from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field,
    field_validator,
)
from .models import Rating, RatingType

class RatingReviewSchema(BaseModel):
    """Schema for submitting a rating for a Hotel, Room, or Property"""
    asset_type: Literal['hotel', 'room', 'property'] = Field(
        ..., 
        description="Type of asset being rated"
    )
    asset_id: int = Field(
        ..., 
        description="ID of the asset being rated"
    )
    comment: str = Field(
        ..., 
        description="Review comment"
    )
    score: int = Field(
        default=5, 
        ge=1, 
        le=5,
        description="Rating score from 1 to 5"
    )

    @field_validator('asset_type')
    @classmethod
    def validate_asset_type(cls, v):
        if v not in ['hotel', 'room', 'property']:
            raise ValueError("asset_type must be 'hotel', 'room', or 'property'")
        return v

    model_config = ConfigDict(from_attributes=True)


class RatingResponseSchema(BaseModel):
    """Schema for returning a rating"""
    id: Optional[int] = None
    comment: str
    score: int
    asset_type: str = Field(description="Type of rated asset")
    asset_id: int = Field(description="ID of the rated asset")
    commenter: Optional[dict] = Field(None, description='Details of the commenter')
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_relations(cls, rating: Rating):
        """Transform ORM object to response schema with all relationships resolved"""
        asset_type = rating.rateable_type.value if hasattr(rating.rateable_type, 'value') else str(rating.rateable_type)
        
        return cls(
            id=rating.id,
            comment=rating.comment,
            score=rating.score,
            asset_type=asset_type,
            asset_id=rating.rateable_id,
            commenter=(
                {
                    "profile_avatar_url": getattr(commenter, 'profile_avatar_url', None) or "",
                    "name": f"{commenter.first_name} {commenter.last_name}"
                }
                if (commenter := rating.commenter)
                else None
            ),
            created_at=rating.created_at.isoformat() if rating.created_at else None
        )


class RatingListSchema(BaseModel):
    """Schema for listing ratings"""
    total: int = Field(description="Total number of ratings")
    average_score: float = Field(description="Average score")
    ratings: list[RatingResponseSchema] = Field(description="List of ratings")