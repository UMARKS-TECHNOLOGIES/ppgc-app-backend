from typing import Optional, Literal
from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field,
)
from .models import Rating

class RatingReviewSchema(BaseModel):
    asset_to_rate:str =  'Area'
    comment: str
    score: int = 0
    hotel_id: Optional[int] = Field(None, description="id of the hotel to rate")
    area_id: Optional[int] = Field(None, description='database id of the area to rate.')

    model_config = ConfigDict(from_attributes=True)

class RatingResponseSchema(BaseModel):
    comment: str
    score: int = 0
    commenter: Optional[dict] = Field(None, description='details of the commenter')

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_relations(cls, rating: Rating):
        """Transform ORM object to response schema with all relationships resolved"""
        return cls(
            comment=rating.comment,
            score=rating.score,
            commenter=(
                {
                    "profile_avatar_url": commenter.profile_avatar_url or "",
                    "name": f"{commenter.first_name} {commenter.last_name}"
                }
                if (commenter := rating.commenter)
                else None
            )
        )