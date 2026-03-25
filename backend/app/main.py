from fastapi import FastAPI

app = FastAPI(
    title="DataSpy Decision AI Backend",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "message": "DataSpy Decision AI backend is running"
    }