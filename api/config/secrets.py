from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):

    # Worker configuration
    LOG_LEVEL: str
    MODEL_NAME: str

    # ElasticSerch variables used by elsticsearch service
    ELASTIC_CLUSTER: List[str]
    ELASTIC_PRT: str
    ELASTIC_USR: str
    ELASTIC_PSW: str
    ELASTIC_PAGE_SIZE: int

    # MinIO variables used by MinIO service
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

    # LLM variables
    VLLM_TENSOR_PARALLEL_SIZE: int = 1
    VLLM_PIPELINE_PARALLEL_SIZE: int = 1
    VLLM_QUANTIZATION: Optional[str] = None
    VLLM_ENFORCE_EAGER: Optional[bool] = None
    VLLM_MAX_SEQ_LEN_TO_CAPTURE: int = 8192
    VLLM_DISABLE_CUSTOM_ALL_REDUCE: bool = False
    VLLM_MEMORY_UTILIZATION: float = 0.9
    VLLM_MAX_MODEL_LEN: int = 9000
    VLLM_MAX_NUM_BATCHED_TOKENS: int = 2048
    VLLM_MAX_NUM_SEQS: int = 256
    VLLM_ENABLE_CHUNKED_PREFILL: bool = False

    # VLLM variables
    VLLM_WORKER_MULTIPROC_METHOD: str = "fork"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
