import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.models import User
from ppgc_backend.config.settings import (
    SUPER_ADMIN_PASSWORD,
    SUPER_ADMIN_EMAIL_ADDRESS,
)
from ppgc_backend.app.controllers.auth.services import authenticate_user
from ppgc_backend.config.postgres_connection_manager import get_postgres_instance


@pytest.mark.asyncio
async def test_admin_acc_setup(app_subprocess):
    email=SUPER_ADMIN_EMAIL_ADDRESS
    password=SUPER_ADMIN_PASSWORD
    async with get_postgres_instance() as test_db:
        test_db: AsyncSession 
        query = await test_db.execute(
            select(User)
            .where(
                User.email == email,
                User.is_admin == True,
            )
        )
        admin: User = query.scalars().first()
        assert admin
        user = await authenticate_user(test_db, admin.email, password=password)
        assert user