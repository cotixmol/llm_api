from vllm import SamplingParams, LLM
from api.config.logger import logger
from typing import Dict, List


class VLLMException(Exception):
    pass


class VLLMService:
    def __init__(self, vllm_instance: LLM) -> None:
        self.vllm_instance = vllm_instance
        logger.info(
            f"[VLLM DEBUG] Model initialized. Instance type: {type(self.vllm_instance)}"
        )

    async def generate_text(
        self,
        requests: List[List[Dict[str, str]]],
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
                f"Generating text for {len(requests)} prompts with sampling parameters: "
                f"temperature={temperature}, top_p={top_p}, max_tokens={max_tokens}"
            )
            generations = self.vllm_instance.chat(
                requests, sampling_params=sampling_params
            )

            response = {"outputs": [], "general_info": {}}  # GENERAL INFO IS EMPTY
            # Add general info to the response base on settings in the future

            for idx, generation in enumerate(generations):
                try:
                    text = generation.outputs[0].text
                    response["outputs"].append({"text": text})
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
