# FastApi user routes
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List, Any

from backend.db.schema import SessionLocal
from backend.services.user_service import UserService
from backend.models.user import UserCreate, UserRead, UserUpdate, Category, Tag, Token
from backend.services.user_auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    userAuthService,
    get_current_active_user
)

router = APIRouter()


def get_user_service():
    """Dependency to get UserService with proper session management"""
    session = SessionLocal()
    try:
        yield UserService(session=session)
    finally:
        session.close()


def get_userAuth_service():
    """Dependency to get userAuthService with proper session management"""
    session = SessionLocal()
    try:
        yield userAuthService(session=session)
    finally:
        session.close()


@router.get("/")
async def root():
    return {"Hello": "World"}


@router.get("/users", response_model=list[UserRead])
def get_users(service: UserService = Depends(get_user_service)):
    try:
        return service.list_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: Annotated[UserRead, Depends(get_current_active_user)]):
    return current_user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", response_model=UserRead)
def create_user(user: UserCreate, service: UserService = Depends(get_user_service), auth_service: userAuthService = Depends(get_userAuth_service)):
    try:
        existing_user = service.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(
                status_code=400, detail="Username already registered")

        # Hash the password and create a new UserCreate object with the hashed password
        hashed_password = auth_service.get_password_hash(user.password)
        user_with_hashed_password = UserCreate(
            username=user.username,
            email=user.email,
            password=hashed_password,  # Replace plain password with hashed
            full_name=user.full_name
        )
        return service.create_user(user_with_hashed_password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: userAuthService = Depends(get_userAuth_service)) -> Token:
    try:
        user = service.authenticated_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401,
                                detail="Incorrect username or password",
                                headers={"WWW-Authenticate": "Bearer"},)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = service.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires)
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_token(current_user: Annotated[UserRead, Depends(get_current_active_user)], service: userAuthService = Depends(get_userAuth_service)) -> Token:
    """Refresh access token for authenticated user"""
    try:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = service.create_access_token(
            data={"sub": current_user.username}, expires_delta=access_token_expires)
        return Token(access_token=access_token, token_type="bearer")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me/items/")
async def read_own_items(current_user: Annotated[UserRead, Depends(get_current_active_user)]):
    # TODO: Implement item retrieval
    return [{"item_id": "Foo", "owner": current_user.username}]


@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserUpdate, service: UserService = Depends(get_user_service)):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        #set user values
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        updated_user = service.update_user(user.id, update_data)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _convert_categories(categories: list[dict] | list[Category]) -> list[Category]:
    return [
        category if isinstance(category, Category) else Category(**category)
        for category in categories
    ]


def _convert_tags(tags: list[dict] | list[Tag]) -> list[Tag]:
    return [
        tag if isinstance(tag, Tag) else Tag(**tag)
        for tag in tags
    ]


@router.get("/users/{user_id}/categories", response_model=list[Category])
async def get_user_categories(user_id: int, service: UserService = Depends(get_user_service)):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return _convert_categories(service.get_categories(user.id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/tags", response_model=list[Tag])
async def get_user_tags(user_id: int, service: UserService = Depends(get_user_service)):
    try:
        user = service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _convert_tags(service.get_tags(user.id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/categories", response_model=Category)
async def create_user_categories(user_id: int, category: Category, service: UserService = Depends(get_user_service)):
    try:
        created_categories = service.create_category(user_id, category)
        if created_categories is None:
            raise HTTPException(status_code=404, detail="User not found")
        return Category(**created_categories)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/tags", response_model=Tag)
async def create_user_tags(user_id: int, tag: Tag, service: UserService = Depends(get_user_service)):
    try:
        created_tag = service.create_tag(user_id, tag)
        if created_tag is None:
            raise HTTPException(status_code=404, detail="User not found")
        return Tag(**created_tag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}/categories/{category_name}", response_model=List[Category])
async def delete_user_category(user_id: int, category_name: str, service: UserService = Depends(get_user_service)):
    try:
        deleted_categories = service.delete_category(user_id, category_name)
        if deleted_categories is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _convert_categories(deleted_categories)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/tags/{tag_name}", response_model=List[Tag])
async def delete_user_tag(user_id: int, tag_name: str, service: UserService = Depends(get_user_service)):
    try:
        deleted_tags = service.delete_tag(user_id, tag_name)
        if deleted_tags is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _convert_tags(deleted_tags)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
