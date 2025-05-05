import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from api.config.logger import logger
from typing import Optional
import gc


class LLMException(Exception):
    pass


######################################
# THIS CLASS AND SERVICE ARE DEPRECATED #
######################################


class LLMService:
    def __init__(self, model_path: str) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, device_map="auto", use_cache=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, use_fast=True, device_map="auto", padding_side="left"
        )
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.bfloat16,
            return_full_text=False,
        )

    async def generate_text(
        self, prompt: str, max_new_tokens: Optional[int] = 10000, batch_size: int = 1
    ) -> str:
        try:
            with torch.no_grad():
                response = self.pipe(
                    prompt, max_new_tokens=max_new_tokens, batch_size=batch_size
                )
                torch.cuda.empty_cache()
                gc.collect()
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")
