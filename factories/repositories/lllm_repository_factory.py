from core.repositories.llm_repository import LLMRepository
from api.config.secrets import MODEL_NAME

MODEL_PATH = f"models/{MODEL_NAME}"
def get_llm_repository():
    try:
        return LLMRepository(MODEL_PATH)
    except Exception as error:
        raise error
    