from typing import List
from services.embedding_service import EmbeddingService  # Asume que tienes un servicio para el modelo
from api.config.logger import logger


class EmbeddingRepository:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def get_embedding(self, text: str) -> List[float]:
        """
        Genera un embedding para el texto dado usando el servicio de embeddings.
        """
        logger.info(f"EMBEDDING REPOSITORY OK. Input text: {text}")
        return await self.embedding_service.get_embedding(text)