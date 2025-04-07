import multiprocessing
import torch.multiprocessing as mp
import os
from api.config.secrets import settings as s

multiprocessing.set_start_method('spawn', force=True)
mp.set_start_method('spawn', force=True)
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = s.VLLM_WORKER_MULTIPROC_METHOD



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.topic_router import topic_router
from api.routes.llm_router import llm_router
from api.routes.vectorized_search_router import vectorized_search_router
from api.config.settings import VERSION
from api.config.settings import minio_client
from factories.services.llm_client_initialization import initilialize_llm_client
from contextlib import asynccontextmanager
from factories.services.embedding_client_factory import initialize_embedding_client

description = """# API overview
> Reports and visualizations for RD APP.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    minio_client.update_model_folder(model_name=s.MODEL_NAME, bucket=s.MINIO_BUCKET)
    MODEL_PATH = f"models/{s.MODEL_NAME}"
    app.state.llm_service = initilialize_llm_client(model_path=MODEL_PATH)

    #REVISAR LA CARGA DEL MODELO. OBJETIVO: QUE SE CARGUE Y SE DESCARGUE
    minio_client.update_model_folder(model_name=s.EMBEDDING_MODEL_NAME, bucket=s.MINIO_BUCKET)
    #MODEL_PATH_EMBEDDINGS = f"models/{s.EMBEDDING_MODEL_NAME}"
    #app.state.embedding_service = initialize_embedding_client(model_path=MODEL_PATH_EMBEDDINGS)

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

app.include_router(router=topic_router, prefix=('/topics'), tags=["Topics"])
app.include_router(router=llm_router, prefix=('/llm'), tags=["LLM"])
app.include_router(router=vectorized_search_router, prefix=('/vectorsearch'), tags=["VectorSearch"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
