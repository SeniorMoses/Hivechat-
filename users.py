from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user
)
from database import get_db
from models import User
from schemas import (
    LoginRequest,
    SignupRequest,
    LoginResponse,
)
from websocket import manager


router = APIRouter()


@router.post("/signup", response_model=LoginResponse)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    print("1. SIGNUP STARTED")
    print("Username:", data.username)
    print("Email:", data.email)

    try:

        print("2. Running database query...")

        result = await db.execute(
            select(User).where(
                (User.username == data.username)
                | (User.email == data.email)
            )
        )

        print("3. Database query completed")

        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("4. User already exists")

            raise HTTPException(
                status_code=400,
                detail="Username or email already exists",
            )

        print("5. User does not exist")

        print("6. Hashing password...")

        hashed = await hash_password(
            data.password
        )

        print("7. Password hashed successfully")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hashed
        )

        print("8. User object created")

        db.add(user)

        print("9. User added to database session")

        print("10. Committing database...")

        await db.commit()

        print("11. Database commit successful")

        print("12. Refreshing user...")

        await db.refresh(user)

        print(
            "13. User refreshed. ID:",
            user.id
        )

        print("14. Creating access token...")

        token = create_access_token(
            user.id
        )

        print("15. Access token created")

        print("16. SIGNUP SUCCESSFUL")

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except Exception as e:

        print("================================")
        print("SIGNUP ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("================================")

        raise


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    print("LOGIN STARTED")
    print("Username:", data.username)

    try:

        print("Running login database query...")

        result = await db.execute(
            select(User).where(
                User.username == data.username
            )
        )

        print("Login database query completed")

        user = result.scalar_one_or_none()

        if not user:
            print("Login failed: user not found")

            raise HTTPException(
                status_code=401,
                detail="Invalid username or password",
            )

        print("User found. Verifying password...")

        if not await verify_password(
            data.password,
            user.password_hash,
        ):
            print("Login failed: invalid password")

            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
            )

        print("Password verified")

        token = create_access_token(
            user.id
        )

        print("Login successful")

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except Exception as e:

        print("================================")
        print("LOGIN ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("================================")

        raise


@router.get("/users/{user_id}/status")
async def user_status(
    user_id: int
):
    print(
        "Checking online status for user:",
        user_id
    )

    return {
        "user_id": user_id,
        "online": manager.is_online(user_id),
    }


@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(
        "Loading users for current user:",
        current_user.id
    )

    try:

        result = await db.execute(
            select(User).where(
                User.id != current_user.id
            )
        )

        users = result.scalars().all()

        print(
            "Users loaded:",
            len(users)
        )

        return users

    except Exception as e:

        print("================================")
        print("GET USERS ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))
        print("================================")

        raise
