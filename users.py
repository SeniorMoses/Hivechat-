from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from database import get_db
from models import User
from schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
)
from websocket import manager

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            (User.username == data.username)
            | (User.email == data.email)
        )
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists",
        )
    hashed=await hash_password(data.password)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.username == data.username
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not await verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }
    
@router.get("/users/{user_id}/status")
async def user_status(user_id: int):

    return {
        "user_id": user_id,
        "online": manager.is_online(user_id),
    }