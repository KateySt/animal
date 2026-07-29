import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.db.enums import Currency, InvoiceStatus
from app.schemas import HealthLogRead


class InvoiceCreate(BaseModel):
    animal_id: uuid.UUID
    amount: float
    currency: Currency
    health_logs: list[uuid.UUID]


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    animal_id: uuid.UUID
    user_id: uuid.UUID
    amount_in_cents: int
    status: InvoiceStatus
    currency: Currency
    created_at: datetime.datetime
    updated_at: datetime.datetime


class InvoiceWithLogsRead(InvoiceRead):
    health_logs: list[HealthLogRead]


class InvoiceUpdate(BaseModel):
    animal_id: uuid.UUID | None = None
    amount: float | None = None
    currency: Currency | None = None
    health_logs: list[uuid.UUID] | None = None


class ConfirmPaymentRequest(BaseModel):
    confirmation_token_id: str


class ConfirmPaymentResponse(BaseModel):
    status: str
    client_secret: str | None = None
    payment_intent_id: str | None = None
