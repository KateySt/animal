from minio import Minio

from app.core.config import get_minio_config

minio_config = get_minio_config()

client = Minio(
    minio_config.MINIO_HOST,
    access_key=minio_config.MINIO_ACCESS_KEY,
    secret_key=minio_config.MINIO_SECRET_KEY,
    region=minio_config.MINIO_REGION,
    secure=minio_config.MINIO_SECURE,
)
