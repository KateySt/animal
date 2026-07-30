from fastcrud import FastCRUD

from app.db.models import associations
from app.db.models.animal import Animal, AnimalTranslation
from app.db.models.chat_message import ChatMessage
from app.db.models.chat_session import ChatSession
from app.db.models.health_log import HealthLog, HealthLogTranslation
from app.db.models.invoice import Invoice
from app.db.models.oauth_account import OAuthAccount
from app.db.models.permission import Permission
from app.db.models.refresh_token import RefreshToken
from app.db.models.resource import Resource
from app.db.models.role import Role
from app.db.models.stripe_event import StripeEvent
from app.db.models.user import User

animal_crud = FastCRUD(Animal)
animal_translation_crud = FastCRUD(AnimalTranslation)
chat_session_crud = FastCRUD(ChatSession)
chat_message_crud = FastCRUD(ChatMessage)
health_log_crud = FastCRUD(HealthLog)
health_log_translation_crud = FastCRUD(HealthLogTranslation)
invoice_crud = FastCRUD(Invoice)
role_crud = FastCRUD(Role)
permission_crud = FastCRUD(Permission)
resource_crud = FastCRUD(Resource)
refresh_token_crud = FastCRUD(RefreshToken)
stripe_event_crud = FastCRUD(StripeEvent)
user_crud = FastCRUD(User)
oauth_account_crud = FastCRUD(OAuthAccount)
