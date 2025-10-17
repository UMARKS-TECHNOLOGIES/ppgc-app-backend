from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Property
from ppgc_backend.app.initiator import logger
from ppgc_backend.config.settings import DEBUG
from .schemas import PropertyCreate, PropertyUpdate
from ppgc_backend.app.models import Area, CloudImageDetail
from ppgc_backend.log_config.logger_config import log_error

async def create_property(db: AsyncSession, property_data: PropertyCreate) -> Property:
    try:
        dumped_data = property_data.model_dump()
        area_data = dumped_data.pop('area')
        cover = dumped_data.pop('cover_image')
        other_images_data = dumped_data.pop('other_images',None)

        area = Area(**area_data)
        cover_image = CloudImageDetail(**cover)
        other_images = [
            CloudImageDetail(**data)
            for data in other_images_data
        ] if other_images_data else None

        db.add_all([area,cover_image,*other_images])
        await db.flush()
        new_property = Property(
            **dumped_data,
            area_id = area.id,
            cover_image_id = cover_image.id,
            other_images = other_images,
        )
        db.add(new_property)
        await db.commit()
        await db.refresh(new_property)
        return new_property
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while creating property.'
        d_msg = f'{f_msg} Reason: {e}'
        # if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def update_property(db: AsyncSession, property_id: int, property_data: PropertyUpdate) -> Property:
    property_obj = await get_property(db, property_id)
    
    try:
        for field, value in property_data.model_dump(exclude_unset=True).items():
            setattr(property_obj, field, value)
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while updating property.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def delete_property(db: AsyncSession, property_id: int) -> None:
    property = await get_property(db,property_id)
    
    try:
        await db.delete(property)
        await db.commit()
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while deleting property.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def get_property(db: AsyncSession, property_id: int) -> Property:
    try:
        property = await db.get(Property,property_id)
        if not property:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        return property
    except HTTPException as e:
        raise e
    except Exception as e:
        f_msg = 'An error occurred while fetching property.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def list_properties(db: AsyncSession, page: int, size: int) -> list[Property]:
    offset = (page - 1) * size
    try:
        result = await db.execute(
            select(Property)
            .order_by(Property.id.desc())
            .offset(offset)
            .limit(size)
        )
        return result.scalars().all()
    except Exception as e:
        f_msg = 'An error occurred while listing properties.'
        d_msg = f'{f_msg} Reason: {e}'
        #if DEBUG:  
        logger.error(d_msg)
        log_error(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )
