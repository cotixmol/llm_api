from V2.core.services.llm_service.vllm_service import VLLMService
from fastapi import Request


def build_vllm_service(request: Request) -> VLLMService:
    llm_instance = request.app.state.llm_instance
    return VLLMService(vllm_instance=llm_instance)


# TODO: Create a fake service in test or another folder.
def build_fake_llm_service(request: Request):
    llm_instance = request.app.state.llm_instance
    return VLLMService(
        vllm_instance=llm_instance
    )  # This should be an instance of the fake service
