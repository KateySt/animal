from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import BadRequestError, ForbiddenError, NotFoundError, get_stripe_config
from app.db.enums import InvoiceStatus
from app.db.models import HealthLog, Invoice, StripeEvent, User, invoice_crud
from app.schemas.stripe import ConfirmPaymentResponse, InvoiceCreate, InvoiceUpdate, InvoiceWithLogsRead
from app.services.user_service import UserService


class InvoiceService:
    def __init__(self, session: AsyncSession, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service
        self._stripe_handlers: dict = {
            "payment_intent.succeeded": self._handle_payment_success,
            "payment_intent.payment_failed": self._handle_payment_failure,
            "payment_intent.canceled": self._handle_payment_failure,
        }

    async def get_by_id(self, invoice_id: UUID) -> InvoiceWithLogsRead:
        result = await self._session.execute(select(Invoice).where(Invoice.id == invoice_id).options(selectinload(Invoice.health_logs)))
        invoice = result.scalar_one_or_none()
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return InvoiceWithLogsRead.model_validate(invoice)

    async def create(self, payload: InvoiceCreate) -> InvoiceWithLogsRead:
        user = await self._user_service.get_by_animal_id(payload.animal_id)
        result = await self._session.execute(select(HealthLog).where(HealthLog.id.in_(payload.health_logs)))
        health_logs = result.scalars().all()
        invoice = Invoice(
            animal_id=payload.animal_id,
            user_id=user.id,
            status=InvoiceStatus.pending,
            amount_in_cents=Invoice.from_float(payload.amount, payload.currency),
            currency=payload.currency,
            health_logs=list(health_logs),
        )
        self._session.add(invoice)
        await self._session.commit()
        await self._session.refresh(invoice, ["health_logs"])
        return InvoiceWithLogsRead.model_validate(invoice)

    async def get_by_id_for_update(self, invoice_id: UUID) -> Invoice:
        invoice = await self._session.execute(
            select(Invoice).where(Invoice.id == invoice_id).options(selectinload(Invoice.health_logs)).with_for_update()
        )
        invoice = invoice.scalar_one_or_none()
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        if invoice.status != InvoiceStatus.pending:
            raise BadRequestError(f"Invoice is already {invoice.status}")
        return invoice

    async def update(self, invoice_id: UUID, payload: InvoiceUpdate) -> InvoiceWithLogsRead:
        invoice = await self.get_by_id_for_update(invoice_id)

        if payload.animal_id is not None:
            invoice.animal_id = payload.animal_id
            owner = await self._user_service.get_by_animal_id(payload.animal_id)
            invoice.user_id = owner.id

        if payload.currency is not None:
            invoice.currency = payload.currency

        if payload.amount is not None:
            currency = payload.currency if payload.currency is not None else invoice.currency
            invoice.amount_in_cents = Invoice.from_float(payload.amount, currency)

        if payload.health_logs is not None:
            logs_result = await self._session.execute(select(HealthLog).where(HealthLog.id.in_(payload.health_logs)))
            invoice.health_logs = list(logs_result.scalars().all())

        await self._session.commit()
        await self._session.refresh(invoice)
        return InvoiceWithLogsRead.model_validate(invoice)

    async def delete(self, invoice_id: UUID) -> None:
        invoice = await self.get_by_id_for_update(invoice_id)
        await self._session.delete(invoice)
        await self._session.commit()

    async def confirm_payment(self, invoice_id: UUID, confirmation_token_id: str, user: User) -> ConfirmPaymentResponse:
        invoice = await self.get_by_id_for_update(invoice_id)
        if invoice.user_id != user.id:
            raise ForbiddenError("Not your invoice")

        intent = stripe.PaymentIntent.create(
            amount=invoice.amount_in_cents,
            currency=invoice.currency.value,
            confirm=True,
            confirmation_token=confirmation_token_id,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={"invoice_id": str(invoice_id)},
        )

        await self._session.commit()
        return ConfirmPaymentResponse(status=intent.status)

    async def handle_webhook(self, payload: bytes, sig_header: str | None) -> None:
        if not sig_header:
            raise ForbiddenError("Missing signature header")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, get_stripe_config().STRIPE_WEBHOOK_SECRET)
        except stripe.SignatureVerificationError:
            raise ForbiddenError("Invalid signature")

        existing = await self._session.get(StripeEvent, event["id"])
        if existing:
            return

        handler = self._stripe_handlers.get(event["type"])
        if handler:
            await handler(event["data"]["object"].to_dict())

        self._session.add(StripeEvent(event_id=event["id"], event_type=event["type"]))
        await self._session.commit()

    async def _handle_payment_success(self, event_data: dict) -> None:
        invoice_id = event_data.get("metadata", {}).get("invoice_id")
        await invoice_crud.update(self._session, {"status": InvoiceStatus.paid}, commit=False, id=UUID(invoice_id))

    async def _handle_payment_failure(self, event_data: dict) -> None:
        invoice_id = event_data.get("metadata", {}).get("invoice_id")
        await invoice_crud.update(self._session, {"status": InvoiceStatus.cancelled}, commit=False, id=UUID(invoice_id))
