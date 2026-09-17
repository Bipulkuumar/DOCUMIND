from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.schemas.common import StandardResponse
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AppException, UnauthorizedException
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise AppException(
            code="USER_ALREADY_EXISTS",
            message=f"User with email '{body.email}' already exists.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name
    )
    created_user = await repo.create(user)
    return StandardResponse(
        message="User registered successfully",
        data=UserResponse.model_validate(created_user)
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise AppException(
            code="ACCOUNT_DEACTIVATED",
            message="Your account has been deactivated.",
            status_code=status.HTTP_403_FORBIDDEN
        )

    access_token = create_access_token(subject=str(user.id))
    return StandardResponse(
        message="Login successful",
        data=TokenResponse(
            access_token=access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    return StandardResponse(
        data=UserResponse.model_validate(current_user)
    )
