import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router

default_frontend_origins = (
    "https://auralytix-five.vercel.app,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGIN",
        default_frontend_origins
    ).split(",")
    if origin.strip()
] or default_frontend_origins.split(",")

api_app = FastAPI(
    title="Auracle API",
    version="1.0.0"
)

api_app.include_router(router)


@api_app.get("/")
def health_check():

    return {
        "status": "healthy",
        "service": "Auracle API"
    }


app = CORSMiddleware(
    api_app,
    allow_origins=frontend_origins,
    allow_origin_regex=r"https://auralytix-five(?:-[a-z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
