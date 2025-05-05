from fastapi import Depends
from V2.core.services.llm_service.vllm_service_repository import VLLMServiceRepositoryV2
from V2.core.repositories.prompt_repository import PromptRepository
from V2.core.factories.llm.llm_service_factory import build_vllm_service


def build_prompt_repository(llm_service=Depends(build_vllm_service)):
    """
    Factory function to build and return a PromptRepository instance.
    """
    llm_service_repository = VLLMServiceRepositoryV2(llm_service=llm_service)

    return PromptRepository(llm_service_repository)
