from uuid import UUID

from fastapi import APIRouter, Depends, Request
from starlette import status

from app.core.dependencies import get_current_user, require_roles
from app.db.models import User
from app.schemas import Principal
from app.schemas.stripe import ConfirmPaymentRequest, ConfirmPaymentResponse, InvoiceCreate, InvoiceUpdate, InvoiceWithLogsRead
from app.services import InvoiceService, get_invoice_service

router = APIRouter()


@router.post("/", response_model=InvoiceWithLogsRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    _: Principal = Depends(require_roles("vet")),
) -> InvoiceWithLogsRead:
    return await service.create(payload)


@router.get("/{invoice_id}", response_model=InvoiceWithLogsRead)
async def get_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    _: User = Depends(get_current_user),
) -> InvoiceWithLogsRead:
    return await service.get_by_id(invoice_id)


@router.patch("/{invoice_id}", response_model=InvoiceWithLogsRead)
async def update_invoice(
    invoice_id: UUID,
    payload: InvoiceUpdate,
    service: InvoiceService = Depends(get_invoice_service),
    _: Principal = Depends(require_roles("vet")),
) -> InvoiceWithLogsRead:
    return await service.update(invoice_id, payload)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    _: Principal = Depends(require_roles("vet")),
) -> None:
    await service.delete(invoice_id)


@router.post("/{invoice_id}/confirm", response_model=ConfirmPaymentResponse, status_code=status.HTTP_200_OK)
async def confirm_invoice_payment(
    invoice_id: UUID,
    body: ConfirmPaymentRequest,
    service: InvoiceService = Depends(get_invoice_service),
    user: User = Depends(get_current_user),
) -> ConfirmPaymentResponse:
    return await service.confirm_payment(invoice_id, body.confirmation_token_id, user)


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
    request: Request,
    service: InvoiceService = Depends(get_invoice_service),
) -> None:
    await service.handle_webhook(await request.body(), request.headers.get("Stripe-Signature"))
