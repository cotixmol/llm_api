from V2.core.services.llm_service.vllm_service import VLLMService
from api.config.secrets import settings
from vllm import LLM, SamplingParams
import torch


def build_vllm_service() -> VLLMService:
    llm_instance = LLM(
        model=settings.LLM_MODEL_PATH,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        tensor_parallel_size=settings.VLLM_TENSOR_PARALLEL_SIZE,
        pipeline_parallel_size=settings.VLLM_PIPELINE_PARALLEL_SIZE,
        quantization=settings.VLLM_QUANTIZATION,
        enforce_eager=settings.VLLM_ENFORCE_EAGER,
        max_seq_len_to_capture=settings.VLLM_MAX_SEQ_LEN_TO_CAPTURE,
        disable_custom_all_reduce=settings.VLLM_DISABLE_CUSTOM_ALL_REDUCE,
        gpu_memory_utilization=settings.VLLM_MEMORY_UTILIZATION,
        max_model_len=settings.VLLM_MAX_MODEL_LEN,
        max_num_batched_tokens=settings.VLLM_MAX_NUM_BATCHED_TOKENS,
        max_num_seqs=settings.VLLM_MAX_NUM_SEQS,
        enable_chunked_prefill=settings.VLLM_ENABLE_CHUNKED_PREFILL,
    )
    return VLLMService(llm_instance=llm_instance)
