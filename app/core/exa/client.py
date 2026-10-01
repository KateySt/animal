from functools import lru_cache

from exa_py import AsyncExa

from app.core.config import get_exa_config


@lru_cache
def get_exa_client() -> AsyncExa:
    return AsyncExa(api_key=get_exa_config().EXA_API_KEY)
