import logging
from services.llm_service import LlmService

def get_llm_client():
    try:
        return LlmService(model_path=MODEL_PATH)
    except ValueError as error:
        logging.error(error)
        raise "error loading model"