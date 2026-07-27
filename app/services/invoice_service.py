from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from stripe.checkout import Session

from app.core import BadRequestError, ForbiddenError, NotFoundError, get_stripe_config, log
from app.db.enums import InvoiceStatus
from app.db.models import Invoice, User, invoice_crud
from app.schemas.stripe import InvoiceCreate, InvoiceCreateModel, InvoicePaymentRequest, InvoiceRead, \
    InvoiceWithLogsRead
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
        result = await self._session.execute(
            select(Invoice).where(Invoice.id == invoice_id).options(selectinload(Invoice.health_logs)))
        invoice = result.scalar_one_or_none()
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return InvoiceWithLogsRead.model_validate(invoice)

    async def create(self, payload: InvoiceCreate) -> InvoiceRead:
        user = await self._user_service.get_by_animal_id(payload.animal_id)
        return await invoice_crud.create(
            self._session,
            InvoiceCreateModel(
                **payload.model_dump(), user_id=user.id, status=InvoiceStatus.pending,
                amount_in_cents=Invoice.from_float(payload.amount)
            ),
            schema_to_select=InvoiceRead,
        )

    async def create_checkout_session(self, payload: InvoicePaymentRequest, user: User) -> Session:
        invoice = await self.get_by_id(payload.id)

        if invoice.status != InvoiceStatus.pending:
            raise BadRequestError(f"Invoice is already {invoice.status}")

        logs_list_str = '; '.join([f'{log.procedure_name}: {log.examination_findings}' for log in invoice.health_logs])

        return stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": invoice.currency,
                        "product_data": {
                            "name": "Invoice",
                            "description": f"Invoice for: {logs_list_str}"
                        },
                        "unit_amount": invoice.amount_in_cents,
                    },
                    "quantity": invoice.health_logs.count(),
                }
            ],
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

    async def update(self, payload: dict, sig_header: str) -> None:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, get_stripe_config().STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise ForbiddenError("Invalid signature")

        event_type = event["type"]
        if event_type in self.STRIPE_HANDLERS:
            handler = self.STRIPE_HANDLERS[event_type]
            event_data = event["data"]["object"]
            await handler(event_data)
