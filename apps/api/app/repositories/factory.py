from app.core.config import settings
from app.repositories.local_store import LocalStoreRepository


def get_repository():
    if settings.use_mock_services:
        return LocalStoreRepository()
    from app.repositories.postgres_store import PostgresStoreRepository

    return PostgresStoreRepository()
