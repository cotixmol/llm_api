from fastapi import Depends
from services.embedding_service import EmbeddingService
from core.repositories.embedding_repository import EmbeddingRepository
from api.config.secrets import settings as s
from factories.services.embedding_client_factory import initialize_embedding_client

def get_embedding_model_path() -> str:
    return f"models/{s.EMBEDDING_MODEL_NAME}"

def get_embedding_service(
    model_path: str = Depends(get_embedding_model_path)
) -> EmbeddingService:
    return initialize_embedding_client(model_path)

def get_embedding_repository(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> EmbeddingRepository:
    return EmbeddingRepository(embedding_service)
