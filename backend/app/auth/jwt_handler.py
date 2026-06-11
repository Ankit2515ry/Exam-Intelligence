from datetime import datetime, timedelta

from jose import jwt, JWTError

from dotenv import load_dotenv

import os


# Load environment variables
load_dotenv()


# Secret configuration
SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)


# ====================================
# CREATE JWT TOKEN
# ====================================
def create_access_token(data: dict):

    # Copy payload data
    to_encode = data.copy()

    # Token expiry time
    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Add expiry into payload
    to_encode.update({
        "exp": expire
    })

    # Generate JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ====================================
# VERIFY JWT TOKEN
# ====================================
def verify_token(token: str):

    try:

        # Decode JWT token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Extract email
        email = payload.get("sub")

        return email

    except JWTError:

        return None