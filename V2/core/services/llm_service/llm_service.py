import torch
from vllm import LLM, SamplingParams
from api.config.logger import logger
from typing import Optional, Dict, List
from api.config.secrets import settings as s


class LLMException(Exception):
    pass


class LLMService:
    def __init__(self, model_path: str) -> None:
        # Instanciate the LLM with device and configuration settings.
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.llm = LLM(
            model=model_path,
            device=self.device,
            tensor_parallel_size=s.VLLM_TENSOR_PARALLEL_SIZE,
            pipeline_parallel_size=s.VLLM_PIPELINE_PARALLEL_SIZE,
            quantization=s.VLLM_QUANTIZATION,
            enforce_eager=s.VLLM_ENFORCE_EAGER,
            max_seq_len_to_capture=s.VLLM_MAX_SEQ_LEN_TO_CAPTURE,
            disable_custom_all_reduce=s.VLLM_DISABLE_CUSTOM_ALL_REDUCE,
            gpu_memory_utilization=s.VLLM_MEMORY_UTILIZATION,
            max_model_len=s.VLLM_MAX_MODEL_LEN,
            max_num_batched_tokens=s.VLLM_MAX_NUM_BATCHED_TOKENS,
            max_num_seqs=s.VLLM_MAX_NUM_SEQS,
            enable_chunked_prefill=s.VLLM_ENABLE_CHUNKED_PREFILL,
        )
        logger.info(
            f"[VLLM DEBUG] Model initialized on {self.device}. Instance type: {type(self.llm)}"
        )

    async def generate_text(
        self,
        prompts: List[List[Dict[str, str]]],
        **kwargs,
    ) -> dict:
        try:
            MAX_TOKENS = 40
            TEMPERATURE = 0.0
            TOP_P = 1.0
            sampling_params = SamplingParams(
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=MAX_TOKENS
            )
            logger.info(
                f"Generating text for {len(prompts)} prompts with sampling parameters: "
                f"temperature={TEMPERATURE}, top_p={TOP_P}, max_tokens={MAX_TOKENS}"
            )
            generations = self.llm.chat(prompts, sampling_params=sampling_params)
            response = {"outputs": [], "general_info": {}}

            for idx, generation in enumerate(generations):
                try:
                    text = generation.outputs[0].text
                    total_prompt_time = (
                        generation.metrics.finished_time
                        - generation.metrics.arrival_time
                    )
                    response["outputs"].append(
                        {"text": text, "other_info": {"prompt_time": total_prompt_time}}
                    )
                    logger.debug(
                        f"Generation {idx + 1}: produced text (prompt_time={total_prompt_time:.3f}s)."
                    )
                except Exception as inner_error:
                    logger.error(
                        f"Error processing generation {idx + 1}: {inner_error}",
                        exc_info=True,
                    )
                    # Append an empty result so the response list maintains the same size as prompts.
                    response["outputs"].append(
                        {"text": "", "other_info": {"prompt_time": None}}
                    )
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")

    async def test_model(self, prompt: str) -> dict:
        sampling_params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=1000000)
        generations = self.llm.chat(prompt, sampling_params=sampling_params)
        return generations
