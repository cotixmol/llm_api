import torch
from vllm import LLM, SamplingParams
from api.config.logger import logger
from typing import Optional, Dict, List
from api.config.secrets import settings as s


class LLMException(Exception):
    pass

class LLMService:
    def __init__(self, model_path: str) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.llm = LLM(
            model=model_path, 
            device=self.device, 
            tensor_parallel_size=s.VLLM_TENSOR_PARALLEL_SIZE, 
            quantization=s.VLLM_QUANTIZATION, 
            enforce_eager=s.VLLM_ENFORCE_EAGER, 
            max_seq_len_to_capture=s.VLLM_MAX_SEQ_LEN_TO_CAPTURE, 
            disable_custom_all_reduce=s.VLLM_DISABLE_CUSTOM_ALL_REDUCE, 
            memory_utilization=s.VLLM_MEMORY_UTILIZATION
        )
    
    async def generate_text(
            self, 
            prompts: List[List[Dict[str, str]]], 
            max_new_tokens: Optional[int] = 10000,
            temperature: Optional[float] = 0.6,
            top_p: Optional[float] = 0.9,
            **kwargs
            ) -> dict:
        try:
            sampling_params = SamplingParams(temperature=temperature, top_p=top_p, max_tokens=max_new_tokens)
            generations = self.llm.chat(prompts, sampling_params=sampling_params)
            response = {
                "outputs": [],
                "general_info": {}
            }
            for generation in generations:
                text = generation.outputs[0].text
                total_prompt_time = generation.metrics.finished_time - generation.metrics.arrival_time
                response["outputs"].append(
                    {
                        "text": text,
                        "other_info": {
                            "prompt_time": total_prompt_time
                        }
                    }
                )
                
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")