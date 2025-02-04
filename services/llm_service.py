import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from api.config.logger import logger


class LLMException(Exception):
    pass

class LLMService:
    def __init__(self, model_path: str) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.pipe = pipeline("text-generation", 
                                model=self.model, 
                                tokenizer=self.tokenizer,
                                torch_dtype=torch.bfloat16,
                                return_full_text=False)
    
    async def generate_text(self, prompt: str, max_new_tokens: int) -> str:
        try:
            response = self.pipe(prompt, max_new_tokens=max_new_tokens)
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")
        
    