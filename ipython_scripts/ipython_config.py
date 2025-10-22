import asyncio
from sqlalchemy.future import select
from IPython import get_ipython  # Import IPython for interactive use
from sqlalchemy.orm import joinedload
from sqlalchemy import delete, insert

from ppgc_backend.app.database import AsyncSessionLocal
from ppgc_backend.app.models import (
    User,
)
from ppgc_backend.app.controllers.auth.services import (
    get_password_hash,
    create_user,
)
from ppgc_backend.app.controllers.auth.services import (
    UserRegistrationSchema,
)

async def setup():
    # Create a new database session
    async with AsyncSessionLocal() as db:
        # Add the session and models to the IPython user namespace
        ipython = get_ipython()
        # Bind database session and models to IPython namespace
        ipython.user_ns['db'] = db
        ipython.user_ns['select'] = select
        ipython.user_ns['insert'] = insert
        ipython.user_ns['delete'] = delete
        ipython.user_ns['joinedload'] = joinedload
        ipython.user_ns['User'] = User
        ipython.user_ns['UserRegistrationSchema'] = UserRegistrationSchema
        ipython.user_ns['get_password_hash'] = get_password_hash
        ipython.user_ns['create_user'] = create_user


        print("Database session 'db' and models are available.")
        
# Start the event loop and run the setup function
asyncio.run(setup())

# To begin a new transaction with this Session,
# first issue db.rollback()
