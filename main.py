import uvicorn
from fastapi import FastAPI
from app.database import Base, engine
from app.routers import router
from starlette.middleware.sessions import SessionMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="JjMygGUWvH7nmmHRZ9N8fADwhFa0Xaze0vk_1ESk4Vw")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)