from V2.core.services.llm_service.vllm_service import VLLMService
from V2.api.config.secrets import secrets
from V2.api.config.settings import node_config
from fastapi import Request
from vllm import LLM
import torch


def initialize_vllm_instance():
    vllm_instance = LLM(
        device=node_config["vllm_params"]["device"],
        model=f"models/{node_config['llm_model_name']}",
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

    return vllm_instance


def build_vllm_service(request: Request) -> VLLMService:
    llm_instance = request.app.state.llm_instance
    return VLLMService(vllm_instance=llm_instance)
