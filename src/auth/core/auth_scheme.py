from typing import Annotated

from fastapi import Depends, Request, HTTPException, status
from fastapi.security.oauth2 import OAuth2Model
from fastapi.security.base import SecurityBase

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.users.models import UserORM

from .auth_backend import AuthBackend


class AuthScheme(SecurityBase):
    def __init__(self, backend: AuthBackend):

        super().__init__()

        self.backend = backend
        self.get_async_session = get_async_session

        self.model = OAuth2Model(flows={})  # type: ignore
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request, session: Annotated[AsyncSession, Depends(get_async_session)]) -> UserORM:
        unauthorized_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

        token = self.backend.transport.get_token(request)

        if token is None:
            raise unauthorized_exc

        user_data = self.backend.strategy.decode(token)

        if user_data is None:
            raise unauthorized_exc

        query = select(UserORM).where(UserORM.id == user_data.get("id")).limit(1)
        result = (await session.execute(query)).scalar_one_or_none()

        if result is None:
            raise unauthorized_exc

        return result

    async def current_user_or_none(self, session: Annotated[AsyncSession, Depends(get_async_session)],
                                   request: Request) -> UserORM | None:
        token = self.backend.transport.get_token(request)

        if token is None:
            return None

        user_data = self.backend.strategy.decode(token)

        if user_data is None:
            return None

        query = select(UserORM).where(UserORM.id == user_data.get("id")).limit(1)
        result = (await session.execute(query)).scalar_one_or_none()

        return result


class AuthSchemeAdmin(AuthScheme):
    def __init__(self, backend: AuthBackend):
        super().__init__(backend)

    async def __call__(self, request: Request, session: Annotated[AsyncSession, Depends(get_async_session)]) -> UserORM:
        unauthorized_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

        token = self.backend.transport.get_token(request)

        if token is None:
            raise unauthorized_exc

        user_data = self.backend.strategy.decode(token)

        if user_data is None:
            raise unauthorized_exc

        if user_data.get("adm") is None or not user_data.get("adm"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN
            )

        query = select(UserORM).where(UserORM.id == user_data.get("id")).limit(1)
        result = (await session.execute(query)).scalar_one_or_none()

        if result is None:
            raise unauthorized_exc

        return result
