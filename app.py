import multiprocessing
multiprocessing.set_start_method('spawn', force=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.topic_router import topic_router
from api.routes.llm_router import llm_router
from api.config.secrets import settings as s
from api.config.settings import VERSION
from api.config.settings import minio_client
from factories.services.llm_client_initialization import initilialize_llm_client
from contextlib import asynccontextmanager



description = """# API overview
> Reports and visualizations for RD APP.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    minio_client.update_model_folder(model_name=s.MODEL_NAME, bucket=s.MINIO_BUCKET)
    MODEL_PATH = f"models/{s.MODEL_NAME}"
    app.state.llm_service = initilialize_llm_client(model_path=MODEL_PATH)
    yield
    # Shutdown event
    
app = FastAPI(title="RD_APP_REPORTS", description=description, version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=topic_router, prefix=('/topics'), tags=["Topics"])
app.include_router(router=llm_router, prefix=('/llm'), tags=["LLM"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
