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


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    animal_id: uuid.UUID
    user_id: uuid.UUID
    amount_in_cents: int
    currency: Currency
    status: InvoiceStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    health_logs: list[HealthLogRead]


class InvoiceCreateModel(BaseModel):
    animal_id: uuid.UUID
    user_id: uuid.UUID
    amount_in_cents: int
    status: InvoiceStatus
    currency: Currency
    health_logs: list[uuid.UUID]


class InvoicePaymentRequest(BaseModel):
    id: uuid.UUID
    success_url: str = "http://localhost:8000/success"
    cancel_url: str = "http://localhost:8000/cancel"
