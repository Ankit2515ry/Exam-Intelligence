from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.auth.schemas import (
    UserCreate,
    UserLogin
)

from app.db.models.user import User

from app.auth.hashing import (
    hash_password,
    verify_password
)

from app.auth.jwt_handler import (
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================
# SIGNUP API
# =========================
@router.post("/signup")
def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    # Normalize email
    email = user.email.lower().strip()

    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(
        user.password
    )

    # Create new user
    new_user = User(
        name=user.name,
        email=email,
        password=hashed_password
    )

    # Save to database
    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return {
        "message": "User created successfully"
    }


# =========================
# LOGIN API
# =========================
@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    # Normalize email
    email = user.email.lower().strip()

    # Find user by email
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    # Check email exists
    if not existing_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email"
        )

    # Verify password
    valid_password = verify_password(
        user.password,
        existing_user.password
    )

    # Invalid password
    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": existing_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }