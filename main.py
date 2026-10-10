from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware


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
    title="Moses' software",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
