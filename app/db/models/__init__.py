from fastcrud import FastCRUD

from app.db.models import associations
from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog
from app.db.models.oauth_account import OAuthAccount
from app.db.models.permission import Permission
from app.db.models.refresh_token import RefreshToken
from app.db.models.resource import Resource
from app.db.models.role import Role
from app.db.models.user import User

animal_crud = FastCRUD(Animal)
health_log_crud = FastCRUD(HealthLog)
role_crud = FastCRUD(Role)
permission_crud = FastCRUD(Permission)
resource_crud = FastCRUD(Resource)
refresh_token_crud = FastCRUD(RefreshToken)
user_crud = FastCRUD(User)
oauth_account_crud = FastCRUD(OAuthAccount)