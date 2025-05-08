from services.llm_vllm_service import LLMService
from V2.utils.logger import logger


def initilialize_llm_client(model_path: str):
    try:
        logger.info(f"loading model from: {model_path}")
        llm_instance = LLMService(model_path)
        return llm_instance
    except ValueError as error:
        raise f"error loading model: {error}"
