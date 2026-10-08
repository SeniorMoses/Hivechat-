@router.post("/signup", response_model=LoginResponse)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    print("1. SIGNUP STARTED")

    result = await db.execute(
        select(User).where(
            (User.username == data.username)
            | (User.email == data.email)
        )
    )

    print("2. DATABASE QUERY WORKED")

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists",
        )

    print("3. USER DOES NOT EXIST")

    hashed = await hash_password(data.password)

    print("4. PASSWORD HASHED")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed
    )

    db.add(user)

    print("5. USER ADDED")

    await db.commit()

    print("6. DATABASE COMMIT WORKED")

    await db.refresh(user)

    print("7. USER REFRESHED")

    token = create_access_token(user.id)

    print("8. TOKEN CREATED")

    return {
        "access_token": token,
        "token_type": "bearer",
    }
