from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import engine, Base


import users, chat

from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as connection:

        await connection.run_sync(
            Base.metadata.create_all
        )

    yield

    await engine.dispose()


app = FastAPI(
    title="Real-Time Chat API",
    lifespan=lifespan,
)


app.include_router(users.router)
app.include_router(chat.router)





@app.get("/chat")
async def chat_page():
    return FileResponse("index.html")
@app.get("/")
async def root():

    return {
        "message": "Chat server is running"
    }