from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog
from app.db.models.user import User

from fastcrud import FastCRUD

animal_crud = FastCRUD(Animal)
health_log_crud = FastCRUD(HealthLog)
user_crud = FastCRUD(User)