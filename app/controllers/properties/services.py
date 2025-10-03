from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Property
from ppgc_backend.app.models import Area, CloudImageDetail
from .schemas import PropertyCreate, PropertyUpdate


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
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def update_property(db: AsyncSession, property_id: int, property_data: PropertyUpdate) -> Property:
    try:
        result = await db.execute(select(Property).where(Property.id == property_id))
        property_obj = result.scalar_one_or_none()
        if not property_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        for field, value in property_data.model_dump(exclude_unset=True).items():
            setattr(property_obj, field, value)
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while updating property.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def delete_property(db: AsyncSession, property_id: int) -> None:
    try:
        property = await get_property(db,property_id)
        await db.delete(property)
        await db.commit()
    except Exception as e:
        await db.rollback()
        f_msg = 'An error occurred while deleting property.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
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
    except Exception as e:
        f_msg = 'An error occurred while fetching property.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )


async def list_properties(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Property]:
    try:
        result = await db.execute(
            select(Property).offset(skip).limit(limit).order_by(Property.id.desc())
        )
        return result.scalars().all()
    except Exception as e:
        f_msg = 'An error occurred while listing properties.'
        d_msg = f'{f_msg} Reason: {e}'
        print(d_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f_msg
        )
