import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGIN",
        "https://auralytix-five.vercel.app"
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="Auracle API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


@app.get("/")
def health_check():

    return {
        "status": "healthy",
        "service": "Auracle API"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
