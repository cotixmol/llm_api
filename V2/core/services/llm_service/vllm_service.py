import os
from vllm import SamplingParams, LLM
from V2.utils.logger import logger
from V2.api.dtos.prompt_dto import PromptMessageItem
from V2.core.services.llm_service.vllm_tracing import trace_llm_call, trace_llm_prompt
from typing import List
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class VLLMException(Exception):
    pass


class VLLMService:
    def __init__(self, vllm_instance: LLM) -> None:
        self.vllm_instance = vllm_instance
        logger.info(
            f"[VLLM DEBUG] Model initialized. Instance type: {type(self.vllm_instance)}"
        )

    @trace_llm_call
    async def generate_text(
        self,
        prompts: List[List[PromptMessageItem]],
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 40,
    ) -> List[str]:
        """
        Generate text using the VLLM model. This method uses the chat method of the VLLM instance, and expects a list of messages for each request.
        Args:
            requests (List[List[Dict[str, str]]]): List of messages to generate text for.
            temperature (float): Sampling temperature.
            top_p (float): Top-p sampling parameter.
            max_tokens (int): Maximum number of tokens to generate.
        Returns:
            List[str]: List of generated text responses.
        """
        try:
            sampling_params = SamplingParams(
                temperature=temperature, top_p=top_p, max_tokens=max_tokens
            )
            logger.info(
                f"Generating text for {len(prompts)} prompts with sampling parameters: "
                f"temperature={temperature}, top_p={top_p}, max_tokens={max_tokens}"
            )

            generations = self.vllm_instance.chat(
                prompts, sampling_params=sampling_params
            )

            response = {"outputs": [], "general_info": {}}

            for idx, (generation, prompt_messages) in enumerate(
                zip(generations, prompts)
            ):
                try:
                    if os.getenv("ENVIRONMENT") != "local":
                        trace_llm_prompt(generation, prompt_messages)

                    response["outputs"].append({"text": generation.outputs[0].text})
                except Exception as inner_error:
                    logger.error(
                        f"Error processing generation {idx + 1}: {inner_error}",
                        exc_info=True,
                    )
                    response["outputs"].append({"text": ""})

            return response

        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise VLLMException(f"Error generating text: {error}")
