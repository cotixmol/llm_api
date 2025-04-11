from services.embedding_service import EmbeddingService
from api.config.logger import logger

def initialize_embedding_client(model_path: str):
    try:
        logger.info(f"loading model from: {model_path}")
        embedding_instance = EmbeddingService(model_path)
        return embedding_instance
    except ValueError as error:
        raise Exception(f"Error loading model: {error}")