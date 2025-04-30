import os
from api.config.secrets import settings as s
from api.config.settings import node_config

#os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = s.VLLM_WORKER_MULTIPROC_METHOD
tracing_endpoint = f"http://{node_config['tracing_params']['tracing_url']}:{node_config['tracing_params']["tracing_port"]}"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = tracing_endpoint
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from phoenix.otel import register

# If the provider it is not registered before imports, the @tracer.chain decorator gives an error
# because its checks for the default tracer from opentelemetry
# is this the correct way of doing this?
tracer_provider = register(protocol=node_config['tracing_params']['tracing_protocol'], project_name=node_config['tracing_params']['tracing_project_name'], batch=s.TRACING_BATCH_PROCESSOR)
trace.set_tracer_provider(tracer_provider)

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
    # check if model exists and download it
    minio_client.update_model_folder(model_name=node_config["llm_model_name"], bucket=s.MINIO_BUCKET)
    # initialize llm client
    MODEL_PATH = f"models/{node_config["llm_model_name"]}"
    app.state.llm_service = initilialize_llm_client(model_path=MODEL_PATH)

    #REVISAR LA CARGA DEL MODELO. OBJETIVO: QUE SE CARGUE Y SE DESCARGUE
    minio_client.update_model_folder(model_name=node_config["embedding_model_name"], bucket=s.MINIO_BUCKET)
    #MODEL_PATH_EMBEDDINGS = f"models/{s.EMBEDDING_MODEL_NAME}"
    #app.state.embedding_service = initialize_embedding_client(model_path=MODEL_PATH_EMBEDDINGS)

    yield
    
app = FastAPI(title="RD_APP_REPORTS", description=description, version=VERSION, lifespan=lifespan)
# instrument fastapi routes

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

FastAPIInstrumentor().instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
