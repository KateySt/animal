from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin

from app.admin.auth import AdminAuthProvider
from app.admin.views import AnimalAdmin, HealthLogAdmin, PermissionAdmin, UserAdmin
from app.core import auth_config
from app.db.models import User
from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog
from app.db.models.permission import Permission
from app.db.session import engine


def setup_admin(app: FastAPI) -> None:
    app.add_middleware(SessionMiddleware, secret_key=auth_config.ADMIN_SECRET)

    admin = Admin(
        engine,
        title="Animal Shelter",
        base_url="/admin",
        auth_provider=AdminAuthProvider(),
    )

    admin.add_view(UserAdmin(User, icon="fa-solid fa-user", name="User", label="Users"))
    admin.add_view(AnimalAdmin(Animal, icon="fa-solid fa-paw", name="Animal", label="Animals"))
    admin.add_view(HealthLogAdmin(HealthLog, icon="fa-solid fa-notes-medical", name="Health Log", label="Health Logs"))
    admin.add_view(PermissionAdmin(Permission, icon="fa-solid fa-shield-halved", name="Permission", label="Permissions"))

    admin.mount_to(app)
