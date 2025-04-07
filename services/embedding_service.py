from sentence_transformers import SentenceTransformer
from api.config.logger import logger

class EmbeddingService:
    def __init__(self, model_name: str):
        """
        Initialize the embedding model.
        
        :param model_name: Name of the pre-trained model to use for embeddings.
        """
        self.model_name = model_name
        self.model = self._load_model()

    def _load_model(self):
        """
        Load the embedding model.
        
        :return: Loaded SentenceTransformer model.
        """
        try:
            model = SentenceTransformer(self.model_name)
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model '{self.model_name}': {e}")

    async def get_embedding(self, text: str):
        """
        Generate embedding for a given text.
        
        :param text: Input text to generate embedding for.
        :return: Embedding vector.
        """
        logger.info(f"EMBEDDING SERVICE OK")

        if not text:
            raise ValueError("Input text cannot be empty.")
        return self.model.encode(text, convert_to_tensor=True)