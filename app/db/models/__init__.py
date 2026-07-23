from fastcrud import FastCRUD

from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog
from app.db.models.oauth_account import OAuthAccount
from app.db.models.permission import Permission
from app.db.models.user import User

animal_crud = FastCRUD(Animal)
health_log_crud = FastCRUD(HealthLog)
permission_crud = FastCRUD(Permission)
