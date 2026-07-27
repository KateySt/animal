from fastapi import APIRouter, Depends
from fastapi import Request

from app.core.dependencies import require_roles, get_current_user
from app.db.models import User
from app.schemas import Principal
from app.schemas.stripe import InvoicePaymentRequest, InvoiceCreate, InvoiceResponse
from app.services import InvoiceService, get_invoice_service

router = APIRouter()


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    payload: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    _: Principal = Depends(require_roles("vet")),
) -> InvoiceResponse:
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
