from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.schemas import SUser
from src.users.models import UserORM

from . import auth_manager
from .core.password import Password
from .schemas import SUserRegister, SUserLogin


router = APIRouter(prefix="/auth", tags=["Auth"])

routers = (router, )

session_dependency = Annotated[AsyncSession, Depends(get_async_session)]


@router.post("/register", response_model=SUser)
async def register(data: SUserRegister, session: session_dependency):
    query = select(UserORM).where(UserORM.name.ilike(data.name))

    if (await session.execute(query)).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this name already exists"
        )

    user_data = data.dict()
    user_data["password"] = Password.hash(user_data["password"])

    stmt = insert(UserORM).values(user_data).returning(UserORM)
    result = await session.execute(stmt)
    await session.commit()

    return result.scalar_one()


@router.post("/login")
async def login(data: SUserLogin, session: session_dependency):
    query = select(UserORM).where(UserORM.name.ilike(data.name))
    user = (await session.execute(query)).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login or password"
        )

    if not Password.validate(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login or password"
        )

    return await auth_manager.login(user.id)


@router.post("/logout")
async def logout():
    return await auth_manager.logout()
