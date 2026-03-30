from fastapi import FastAPI
from app.api.routes.upload import router as upload_router
from app.api.routes.schema import router as schema_router
from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.profile import router as profile_router
from app.api.routes.insights import router as insights_router
from app.api.routes.narrative import router as narrative_router
from app.api.routes.forecast import router as forecast_router
from app.api.routes.decisions import router as decisions_router
from app.api.routes.analyze import router as analyze_router

app = FastAPI(
    title="DataSpy Decision AI Backend",
    version="0.1.0"
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(schema_router, prefix="/api", tags=["Schema"])
app.include_router(capabilities_router, prefix="/api", tags=["Capabilities"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])
app.include_router(insights_router, prefix="/api", tags=["Insights"])
app.include_router(narrative_router, prefix="/api", tags=["Narrative"])
app.include_router(forecast_router, prefix="/api", tags=["Forecast"])
app.include_router(decisions_router, prefix="/api", tags=["Decisions"])
app.include_router(analyze_router, prefix="/api", tags=["Analyze"])

@app.get("/")
def root():
    return {
        "message": "DataSpy Decision AI backend is running"
    }