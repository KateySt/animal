from fastapi import APIRouter

from app.routers.v1 import (
    animal_router,
    anthropic_chat_router,
    auth_router,
    health_log_router,
    image_router,
    permission_router,
    resource_router,
    role_router,
    stripe_router,
    users_router,
)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
v1_router.include_router(users_router, prefix="/users", tags=["Users"])

v1_router.include_router(resource_router, prefix="/resources", tags=["Resources"])
v1_router.include_router(permission_router, prefix="/permissions", tags=["Permissions"])
v1_router.include_router(role_router, prefix="/roles", tags=["Roles"])

v1_router.include_router(animal_router, prefix="/animals", tags=["Animals"])
v1_router.include_router(health_log_router, prefix="/animals/{animal_id}/health-logs", tags=["Health logs"])
v1_router.include_router(stripe_router, prefix="/stripe", tags=["Stripe"])

v1_router.include_router(anthropic_chat_router, prefix="/anthropic-chat", tags=["Anthropic chat"])

v1_router.include_router(image_router, prefix="/image", tags=["Image"])
