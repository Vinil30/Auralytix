# backend/app.py

from fastapi import FastAPI

from routes.api import router

app = FastAPI(
    title="Auracle API",
    version="1.0.0"
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
