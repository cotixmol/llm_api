from V2.core.services.llm_service.llm_service import LLMService
from api.config.secrets import settings


def build_llm_service() -> LLMService:
    return LLMService(model_path=settings.LLM_MODEL_PATH)
