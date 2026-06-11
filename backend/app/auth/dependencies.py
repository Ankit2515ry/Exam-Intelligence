from fastapi import (
    Depends,
    HTTPException
)

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.auth.jwt_handler import verify_token

from app.db.session import get_db

from app.db.models.user import User


# ====================================
# READ JWT TOKEN FROM HEADER
# ====================================
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/auth/login"
)


# ====================================
# GET CURRENT LOGGED-IN USER
# ====================================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    # Verify JWT token
    email = verify_token(token)

    # Invalid token
    if email is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # Find user in database
    user = db.query(User).filter(
        User.email == email
    ).first()

    # User not found
    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user