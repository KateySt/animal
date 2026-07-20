from fastapi import APIRouter, Depends, status

from app.schemas.animal import AnimalCreate, AnimalResponse
from app.services import get_animal_service
from app.services.animal_service import AnimalService

router = APIRouter()


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    service: AnimalService = Depends(get_animal_service),
) -> AnimalResponse:
    return await service.create_animal_with_initial_health_log(payload)
