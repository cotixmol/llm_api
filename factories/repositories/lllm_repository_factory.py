from core.repositories.llm_repository import LLMRepository
from services.llm_service import LLMService
from api.config.secrets import MODEL_NAME

MODEL_PATH = f"models/{MODEL_NAME}"

def get_llm_repository():
    try:
        llm_service = LLMService(MODEL_PATH)  # Instancia válida de LLMService
        return LLMRepository(llm_service=llm_service)
    except Exception as error:
        raise error
