from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
)

from app.db.models.base import Base


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass
