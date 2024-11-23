from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import auth_manager
from src.auth.core.password import Password
from src.auth.schemas import SUserLogin
from src.database import get_async_session
from src.users.models import UserORM

from .schemas import AdminORM


router = APIRouter(prefix="/admin", tags=["Admin"])
routers = (router, )


@router.post("/login")
async def login(session: Annotated[AsyncSession, Depends(get_async_session)],
                data: SUserLogin):
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong login or password"
    )

    user = (await session.execute(
        select(
            UserORM
        ).where(
            UserORM.name.ilike(data.name)
        )
    )).scalar_one_or_none()

    if user is None:
        raise unauthorized_exc

    admin = (await session.execute(
        select(
            AdminORM
        ).where(
            AdminORM.user_id == user.id
        )
    )).scalar_one_or_none()

    if admin is None:
        raise unauthorized_exc

    if not Password.validate(data.password, user.password):
        raise unauthorized_exc

    return await auth_manager.login(user.id, is_admin=True)
