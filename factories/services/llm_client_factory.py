import api.config.logger as logger
from services.llm_service import LLMService
from api.config.secrets import MODEL_NAME

MODEL_PATH = f"models/{MODEL_NAME}"

def get_llm_client():
    logger.info(f"Loading model from {MODEL_PATH}")
    try:
        return LLMService(model_path=MODEL_PATH)
    except ValueError as error:
        logger.error(error)
        raise "error loading model"