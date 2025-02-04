from services.llm_service import LLMService

def initilialize_llm_client(model_path: str):
    try:
        print(f"loading model from: {model_path}")
        llm_instance = LLMService(model_path)
        return llm_instance
    except ValueError as error:
        raise f"error loading model: {error}"