from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(title="Geo Analytics API", version="1.0.0")

# Dashboard demos are often served from a different origin (e.g. `file://` or a static server).
# Keep this open by default; tighten in production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
