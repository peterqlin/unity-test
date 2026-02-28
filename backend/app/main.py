from fastapi import FastAPI
from app.routers import scene

app = FastAPI(title="Unity Scene Generator API")

app.include_router(scene.router)


@app.get("/")
def hello():
    return {"message": "Hello, world!"}
