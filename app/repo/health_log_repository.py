from app.db.models.health_log import HealthLog
from app.repo.base_repository import BaseRepository


class HealthLogRepository(BaseRepository[HealthLog]):
    model = HealthLog
