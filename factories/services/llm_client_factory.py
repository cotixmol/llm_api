import logging
from services.llm_service import LLMService
from api.config.secrets import MODEL_NAME

MODEL_PATH = f"models/{MODEL_NAME}"

def get_llm_client():
    try:
        return LLMService(model_path=MODEL_PATH)
    except ValueError as error:
        logging.error(error)
        raise "error loading model"