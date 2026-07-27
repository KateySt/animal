from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from stripe.checkout import Session

from app.core import BadRequestError, ForbiddenError, NotFoundError, get_stripe_config, log
from app.db.enums import InvoiceStatus
from app.db.models import HealthLog, Invoice, User, invoice_crud
from app.schemas.stripe import InvoiceCreate, InvoicePaymentRequest, InvoiceWithLogsRead
from app.services.user_service import UserService


class InvoiceService:
    def __init__(self, session: AsyncSession, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service
        self.STRIPE_HANDLERS = {
            "payment_intent.succeeded": self.handle_payment_success,
            "checkout.session.completed": self.handle_payment_success,
            "payment_intent.payment_failed": self.handle_payment_failure,
            "checkout.session.async_payment_failed": self.handle_payment_failure,
            "payment_intent.canceled": self.handle_payment_failure,
            "checkout.session.expired": self.handle_payment_failure,
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
            amount_in_cents=Invoice.from_float(payload.amount),
            currency=payload.currency,
            health_logs=list(health_logs),
        )
        self._session.add(invoice)
        await self._session.commit()
        await self._session.refresh(invoice, ["health_logs"])
        return InvoiceWithLogsRead.model_validate(invoice)

    async def create_checkout_session(self, payload: InvoicePaymentRequest, user: User) -> Session:
        invoice = await self.get_by_id(payload.id)

        if invoice.status != InvoiceStatus.pending:
            raise BadRequestError(f"Invoice is already {invoice.status}")

        logs_list_str = "; ".join([f"{log.procedure_name}: {log.examination_findings}" for log in invoice.health_logs])

        return stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": invoice.currency,
                        "product_data": {"name": "Invoice"},
                        "unit_amount": invoice.amount_in_cents,
                    },
                    "quantity": len(invoice.health_logs),
                }
            ],
            metadata={"invoice_id": str(invoice.id)},
            customer_email=user.email,
            mode="payment",
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )

    async def handle_payment_success(self, event_data: dict):
        log.info(f"Payment successful: {event_data}")
        await invoice_crud.update(self._session, {"status": InvoiceStatus.paid})

    async def handle_payment_failure(self, event_data: dict):
        log.error(f"Payment failed: {event_data}")
        await invoice_crud.update(self._session, {"status": InvoiceStatus.cancelled})

    async def update(self, payload: bytes, sig_header: str) -> None:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, get_stripe_config().STRIPE_WEBHOOK_SECRET)
        except stripe.SignatureVerificationError:
            raise ForbiddenError("Invalid signature")

        event_type = event["type"]
        if event_type in self.STRIPE_HANDLERS:
            handler = self.STRIPE_HANDLERS[event_type]
            event_data = event["data"]["object"]
            await handler(event_data)
