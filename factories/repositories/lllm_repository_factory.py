from core.repositories.llm_repository import LLMRepository

MODEL_PATH = "models/llm_model.pkl"
def get_llm_repository():
    try:
        return LLMRepository(MODEL_PATH)
    except Exception as error:
        raise error
    