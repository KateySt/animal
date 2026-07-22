import uuid

from fastapi_users import FastAPIUsers

from app.db.models.user import User
from app.services.user_manager import get_user_manager, auth_backend

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
