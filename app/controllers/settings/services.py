from sqlalchemy.ext.asyncio import AsyncSession

from ppgc_backend.app.controllers.actors.models import User

async def create_or_update_pass_code(db: AsyncSession, user: User, pass_code: str):
    user.pass_code = pass_code
    db.add(user)
    await db.commit()