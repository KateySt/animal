from app.db.models.animal import Animal
from app.db.models.health_log import HealthLog

from fastcrud import FastCRUD

animal_crud = FastCRUD(Animal)
health_log_crud = FastCRUD(HealthLog)