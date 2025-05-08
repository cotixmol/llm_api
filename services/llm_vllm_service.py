from vllm import LLM, SamplingParams
from V2.utils.logger import logger
from typing import Optional, Dict, List

# from api.config.secrets import settings as s
from api.config.settings import node_config
from openinference.semconv.trace import (
    SpanAttributes,
    OpenInferenceSpanKindValues,
    MessageAttributes,
)
from opentelemetry.trace import Status, StatusCode
from opentelemetry import trace
import json

tracer = trace.get_tracer(__name__)


class LLMException(Exception):
    pass


class LLMService:
    def __init__(self, model_path: str) -> None:
        self.llm = LLM(
            model=model_path,
            tensor_parallel_size=node_config["vllm_params"]["tensor_parallel_size"],
            pipeline_parallel_size=node_config["vllm_params"]["pipeline_parallel_size"],
            quantization=node_config["vllm_params"]["quantization"],
            enforce_eager=node_config["vllm_params"]["enforce_eager"],
            max_seq_len_to_capture=node_config["vllm_params"]["max_seq_len_to_capture"],
            disable_custom_all_reduce=node_config["vllm_params"][
                "disable_custom_all_reduce"
            ],
            gpu_memory_utilization=node_config["vllm_params"]["gpu_memory_utilization"],
            max_model_len=node_config["vllm_params"]["max_model_len"],
            max_num_batched_tokens=node_config["vllm_params"]["max_num_batched_tokens"],
            max_num_seqs=node_config["vllm_params"]["max_num_seqs"],
            enable_chunked_prefill=node_config["vllm_params"]["enable_chunked_prefill"],
        )

    async def generate_text(
        self,
        prompts_list: List[List[Dict[str, str]]],
        max_new_tokens: Optional[int] = 1000,
        temperature: Optional[float] = 0.0,
        top_p: Optional[float] = 1.0,
    ) -> List[str]:
        """
        Generates text using the VLLM model. It uses the "chat" function from LLM class. It can handle multiple prompts at once.
        The function takes a list of prompt messages, each message is a dictionary with "role" and "content" keys.
        Args:
            prompts_list (List[List[Dict[str, str]]]): List of prompt messages.
            max_new_tokens (Optional[int]): Maximum number of tokens to generate.
            temperature (Optional[float]): Sampling temperature.
            top_p (Optional[float]): Top-p sampling parameter.
        Returns:
            list with generated texts.
        """

        try:
            sampling_params = SamplingParams(
                temperature=temperature, top_p=top_p, max_tokens=max_new_tokens
            )
            response = []

            invocation_params = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }

            # Create a span for the entire LLM request
            with tracer.start_as_current_span(
                "LLM Call",
                attributes={
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                    SpanAttributes.LLM_MODEL_NAME: node_config["llm_model_name"],
                    SpanAttributes.LLM_SYSTEM: "vllm",
                    SpanAttributes.LLM_PROVIDER: "self_hosted",
                },
            ) as span:
                for key, value in invocation_params.items():
                    span.set_attribute(
                        f"{SpanAttributes.LLM_INVOCATION_PARAMETERS}.{key}", value
                    )
                span.set_status(Status(status_code=StatusCode.OK))
                generations = self.llm.chat(
                    prompts_list, sampling_params=sampling_params
                )
                for generation, prompt_messages in zip(generations, prompts_list):
                    # add generation to response
                    response.append(generation.outputs[0].text)
                    # Start a child span for this prompt
                    with tracer.start_as_current_span(
                        "LLM Request",
                        attributes={
                            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                            SpanAttributes.LLM_TOKEN_COUNT_PROMPT: len(
                                generation.prompt_token_ids
                            ),
                            SpanAttributes.LLM_TOKEN_COUNT_COMPLETION: len(
                                generation.outputs[0].token_ids
                            ),
                            SpanAttributes.LLM_TOKEN_COUNT_TOTAL: len(
                                generation.prompt_token_ids
                            )
                            + len(generation.outputs[0].token_ids),
                        },
                    ) as span:
                        span.set_attribute(
                            SpanAttributes.INPUT_VALUE,
                            prompt_messages[-1].get(
                                "content", ""
                            ),  # get the last message for input
                        )
                        # OUTPUT_VALUE shows up on the table view under the output column
                        # It also shows up under the `output` tab on the span
                        span.set_attribute(
                            SpanAttributes.OUTPUT_VALUE, generation.outputs[0].text
                        )

                        # LLM_INPUT_MESSAGES shows up under `input_messages` tab on the span page
                        for idx, msg in enumerate(prompt_messages):
                            # Set the role per message
                            span.set_attribute(
                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_ROLE}",
                                msg["role"],
                            )
                            # Set the content per message
                            span.set_attribute(
                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                msg.get("content", ""),
                            )
                        span.set_status(Status(status_code=StatusCode.OK))
            return response
        except Exception as error:
            logger.error(f"Error generating text: {error}")
            raise LLMException(f"Error generating text: {error}")

    async def test_model(self, prompt: str) -> dict:
        sampling_params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=1000000)
        generations = self.llm.chat(prompt, sampling_params=sampling_params)
        return generations

    async def generate_function_call(
        self, messages: List[Dict], tools: List[str]
    ) -> Dict:
        """
        Generate a structured response indicating the function to call and its parameters.
        """
        sampling_params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=1000)
        outputs = self.llm.chat(messages, sampling_params=sampling_params, tools=tools)
        logger.info(f"################Outputs: {outputs}")
        output = outputs[0].outputs[0].text.strip()
        logger.info(f"################Output: {output}")

        return output
