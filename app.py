import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from phoenix.otel import register
from api.config.settings import VERSION, minio_client
from opentelemetry.trace import NoOpTracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from phoenix.otel import register
from V2.api.config.settings import node_config

# If the provider it is not registered before imports, the @tracer.chain decorator gives an error
# because its checks for the default tracer from opentelemetry

if os.getenv("ENVIRONMENT") != "local":
    tracing_endpoint = f"http://{node_config['tracing_params']['tracing_url']}:{node_config['tracing_params']['tracing_port']}"
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = tracing_endpoint
    tracer_provider = register(
        protocol=node_config["tracing_params"]["tracing_protocol"],
        project_name=node_config["tracing_params"]["tracing_project_name"],
        batch=node_config["tracing_params"]["tracing_batch_proccesor"],
    )
else:
    # In local environment, we don't want to use the tracing provider
    tracer_provider = NoOpTracerProvider()


trace.set_tracer_provider(tracer_provider)

from V2.api.config.secrets import secrets
from V2.api.routers.classification_router import classification_router_V2
from V2.api.routers.prompt_router import prompt_router_V2
from V2.api.routers.summary_router import summary_router_V2
from V2.core.factories.llm.fake_llm_instance_factory import initialize_fake_llm_instance
from V2.core.factories.llm.vllm_instance_factory import initialize_vllm_instance
from factories.services.embedding_client_factory import initialize_embedding_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    minio_client.update_model_folder(
        model_name=node_config["llm_model_name"], bucket=secrets.MINIO_BUCKET
    )
    # When in debbuging mode, we use a fake LLM instance.
    # Just change the function to the initialize_fake_llm_instance()
    app.state.llm_instance = initialize_vllm_instance()
    yield


app = FastAPI(title="RD_APP_REPORTS", version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=prompt_router_V2, prefix=("/V2/llm"), tags=["LLM"])
app.include_router(router=classification_router_V2, prefix=("/V2/llm"), tags=["LLM"])
app.include_router(router=summary_router_V2, prefix=("/V2/llm"), tags=["LLM"])

FastAPIInstrumentor().instrument_app(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
