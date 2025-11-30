from fastapi import FastAPI
from app.routers.analyze import router as analyze_router
from app.routers.match import router as match_router

app = FastAPI()

app.include_router(analyze_router, prefix="/api")
app.include_router(match_router, prefix="/api")
