from vllm import SamplingParams, LLM
from api.config.logger import logger
from typing import Optional, Dict, List
from api.config.secrets import settings as s


class VLLMException(Exception):
    pass


class VLLMService:
    def __init__(self, vllm_instance: LLM) -> None:
        self.vllm_instance = vllm_instance
        logger.info(f"[VLLM DEBUG] Model initialized. Instance type: {type(self.vllm_instance)}")

    async def generate_text(
        self,
        prompts: List[List[Dict[str, str]]],
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_new_tokens: int = 40,
    ) -> dict:
        try:
            sampling_params = SamplingParams(
                temperature=temperature, top_p=top_p, max_tokens=max_new_tokens
            )
            logger.info(
                f"Generating text for {len(prompts)} prompts with sampling parameters: "
                f"temperature={temperature}, top_p={top_p}, max_tokens={max_new_tokens}"
            )
            generations = self.vllm_instance.chat(
                prompts, sampling_params=sampling_params
            )
            response = {"outputs": [], "general_info": {}}

            for idx, generation in enumerate(generations):
                try:
                    text = generation.outputs[0].text
                    response["outputs"].append(
                        {"text": text}
                    )
                except Exception as inner_error:
                    logger.error(
                        f"Error processing generation {idx + 1}: {inner_error}",
                        exc_info=True,
                    )
                    # Append an empty result so the response list maintains the same size as prompts.
                    response["outputs"].append(
                        {"text": ""}
                    )
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise VLLMException(f"Error generating text: {error}")
