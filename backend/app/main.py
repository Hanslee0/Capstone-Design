from fastapi import FastAPI

from app.api.evaluate import router as evaluate_router
from app.api.merge import router as merge_router
from app.api.packs import router as packs_router

app = FastAPI(
    title="Border Checker API",
    version="0.1.0",
    description="Policy-based data sovereignty assessment API"
)

app.include_router(merge_router)
app.include_router(packs_router)
app.include_router(evaluate_router)


@app.get("/")
def read_root():
    return {
        "project": "Border Checker",
        "status": "ok",
        "message": "Backend is running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}