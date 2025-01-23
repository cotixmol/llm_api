from fastapi import FastAPI
from api.config.settings import VERSION
from fastapi.middleware.cors import CORSMiddleware
from api.routes.topic_router import topic_router
from api.config.secrets import (MINIO_BUCKET, MODEL_NAME)
from api.config.settings import minio_client


description = """# API overview
> Reports and visualizations for RD APP.
"""

app = FastAPI(title="RD_APP_REPORTS", description=description, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=topic_router, prefix=('/topics'), tags=["Topics"])
app.include_router(router=topic_router, prefix=('/llm'), tags=["Llm"])

def check_models():
    minio_client.update_model_folder(MODEL_NAME, MINIO_BUCKET)

@app.on_event("startup")
async def startup_event():
    check_models()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
