import torch
from elasticsearch import Elasticsearch, NotFoundError, BadRequestError, ConnectionTimeout
from api.dtos.elasticsearch_dtos import IndexStatus, SearchResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging


class LLMException(Exception):
    pass

class LLMService:
    def __init__(self, model_path: str) -> None:
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipe = pipeline("text-generation", 
                                model=self.model, 
                                tokenizer=self.tokenizer, 
                                device=self.device,
                                torch_dtype=torch.bfloat16)
    
    async def generate_text(self, prompt: str, max_new_tokens: int) -> str:
        try:
            print(f"Prompt: {prompt}")
            print(self.device)
            response = self.pipe(prompt, max_new_tokens=max_new_tokens)
            return response[-1]["generated_text"]
        except Exception as error:
            logging.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")
        
    