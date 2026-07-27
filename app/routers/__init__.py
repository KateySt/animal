from fastapi import APIRouter

from app.routers.v1 import auth_router, users_router, resource_router, permission_router, role_router, animal_router, \
    health_log_router, stripe_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
v1_router.include_router(users_router, prefix="/users", tags=["Users"])

v1_router.include_router(resource_router, prefix="/resources", tags=["Resources"])
v1_router.include_router(permission_router, prefix="/permissions", tags=["Permissions"])
v1_router.include_router(role_router, prefix="/roles", tags=["Roles"])

v1_router.include_router(animal_router, prefix="/animals", tags=["Animals"])
v1_router.include_router(health_log_router, prefix="/animals/{animal_id}/health-logs", tags=["Health Logs"])
v1_router.include_router(stripe_router, prefix="/stripe", tags=["Stripe"])
