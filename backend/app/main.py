from fastapi import FastAPI
from app.api.routes.upload import router as upload_router
from app.api.routes.schema import router as schema_router

app = FastAPI(
    title="DataSpy Decision AI Backend",
    version="0.1.0"
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(schema_router, prefix="/api", tags=["Schema"])

@app.get("/")
def root():
    return {
        "message": "DataSpy Decision AI backend is running"
    }