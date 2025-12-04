from datetime import datetime, timedelta, timezone
from typing import Annotated
from sqlalchemy.orm import Session

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from backend.db.schema import User as UserSchema, SessionLocal
from backend.models.user import UserInDB, TokenData

SECRET_KEY = 'f2c04f7076d1c8af03a3220dae3047a02332ca66a98d7be73370c7cba52b0556'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

passwordHash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


class userAuthService:
    def __init__(self, session):
        self.session = session

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return passwordHash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return passwordHash.hash(password)

    def get_user(self, username: str) -> UserInDB | None:
        try:
            user = self.session.query(UserSchema).filter(
                UserSchema.username == username).first()
            if user:
                return UserInDB(**user.__dict__)
            return None
        except Exception as e:
            # Log the error but don't expose internal details
            print(f"Database error in get_user: {e}")
            return None

    def authenticated_user(self, username: str, password: str) -> UserInDB | bool:
        user = self.get_user(username=username)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def get_current_active_user(self, current_user: Annotated[UserInDB, Depends(get_current_user)]) -> UserInDB:
        if current_user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user


# Standalone dependency functions for FastAPI routes
def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> UserInDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    try:
        # Query user from database
        user = db.query(UserSchema).filter(
            UserSchema.username == token_data.username).first()
        if user is None:
            raise credentials_exception
        return UserInDB(**user.__dict__)
    except Exception as e:
        # Log database errors but don't expose them to the client
        print(f"Database error in get_current_user: {e}")
        raise credentials_exception


async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]) -> UserInDB:
    """Get current active user, raise error if disabled"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
