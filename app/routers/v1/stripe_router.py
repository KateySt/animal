from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_current_user, require_roles
from app.db.models import User
from app.schemas import Principal
from app.schemas.stripe import InvoiceCreate, InvoicePaymentRequest, InvoiceWithLogsRead
from app.services import InvoiceService, get_invoice_service

router = APIRouter()


@router.post("/", response_model=InvoiceWithLogsRead)
async def create_invoice(
    payload: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    _: Principal = Depends(require_roles("vet")),
) -> InvoiceWithLogsRead:
    return await service.create(payload)


@router.post("/create-checkout-session")
async def create_checkout_session(
    payload: InvoicePaymentRequest,
    service: InvoiceService = Depends(get_invoice_service),
    user: User = Depends(get_current_user),
) -> str:
    session = await service.create_checkout_session(payload, user)
    return session.url


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    service: InvoiceService = Depends(get_invoice_service),
) -> None:
    await service.update(await request.body(), request.headers.get("Stripe-Signature"))
