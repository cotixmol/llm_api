import torch
from elasticsearch import Elasticsearch, NotFoundError, BadRequestError, ConnectionTimeout
from api.dtos.elasticsearch_dtos import IndexStatus, SearchResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging


class LlmException(Exception):
    pass

class LlmService:
    def __init__(self, model_path: str) -> None:
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = pipeline("text-generation", 
                                 model=self.model, 
                                 tokenizer=self.tokenizer, 
                                 device=self.device,
                                 torch_dtype=torch.bfloat16)
    
    def generate_text(self, prompt: str, max_new_tokens: int) -> str:
        try:
            return self.pipeline(prompt, max_new_tokens, do_sample=True, temperature=0.9)[0]["generated_text"]
        except Exception as error:
            logging.error(f"Error generating text: {error}")
            raise LlmException(f"Error generating text: {error}")
        
    