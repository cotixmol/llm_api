from functools import wraps
from openinference.semconv.trace import (
    SpanAttributes,
    OpenInferenceSpanKindValues,
    MessageAttributes,
)
from opentelemetry.trace import Status, StatusCode
from opentelemetry import trace
from V2.api.config.settings import node_config

tracer = trace.get_tracer(__name__)


def trace_llm_call(func):
    """Decorator to trace LLM calls."""

    @wraps(func)
    async def wrapper(
        self, requests, temperature=0.0, top_p=1.0, max_tokens=40, *args, **kwargs
    ):
        invocation_params = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

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

            # Call the original function
            result = await func(
                self, requests, temperature, top_p, max_tokens, *args, **kwargs
            )
            return result

    return wrapper


def trace_llm_prompt(generation, prompt_messages):
    # Start a child span for this prompt
    with tracer.start_as_current_span(
        "LLM Request",
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
            SpanAttributes.LLM_TOKEN_COUNT_PROMPT: len(generation.prompt_token_ids),
            SpanAttributes.LLM_TOKEN_COUNT_COMPLETION: len(
                generation.outputs[0].token_ids
            ),
            SpanAttributes.LLM_TOKEN_COUNT_TOTAL: len(generation.prompt_token_ids)
            + len(generation.outputs[0].token_ids),
        },
    ) as span:
        span.set_attribute(
            SpanAttributes.INPUT_VALUE,
            prompt_messages[-1].get("content", ""),  # get the last message for input
        )
        # OUTPUT_VALUE shows up on the table view under the output column
        # It also shows up under the `output` tab on the span
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, generation.outputs[0].text)

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
