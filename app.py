import multiprocessing
import torch.multiprocessing as mp
import os
from api.config.secrets import settings as s

multiprocessing.set_start_method('spawn', force=True)
mp.set_start_method('spawn', force=True)
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = s.VLLM_WORKER_MULTIPROC_METHOD



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config.settings import VERSION
from api.config.settings import minio_client
from contextlib import asynccontextmanager

from V2.core.factories.llm_service_factory import initialize_vllm_instance
from V2.api.routers.prompt_router import prompt_router_V2
from V2.api.routers.classification_router import classification_router_V2

description = """# API overview
> Reports and visualizations for RD APP.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    minio_client.update_model_folder(model_name=s.MODEL_NAME, bucket=s.MINIO_BUCKET)
    app.state.llm_service = initialize_vllm_instance()
    yield
    # Shutdown event
    
app = FastAPI(title="RD_APP_REPORTS", description=description, version=VERSION, lifespan=lifespan)

print(f"main.py with :{app}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#app.include_router(router=topic_router, prefix=('/topics'), tags=["Topics"])
#app.include_router(router=llm_router, prefix=('/llm'), tags=["LLM"])

app.include_router(router=prompt_router_V2, prefix=('/V2/llm'), tags=["LLM"])
app.include_router(router=classification_router_V2, prefix=('/V2/classification'), tags=["LLM"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
