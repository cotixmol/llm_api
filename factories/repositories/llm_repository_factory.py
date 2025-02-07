from fastapi import Depends
from core.repositories.llm_repository import LLMRepository
from factories.services.llm_client_factory import get_llm_service
from services.llm_service import LLMService

def get_llm_repository(llm_service: LLMService = Depends(get_llm_service)):
    try:
        return LLMRepository(llm_service=llm_service)
    except Exception as error:
        raise error
