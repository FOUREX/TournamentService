from fastapi import Response

from .auth_backend import AuthBackend
from .auth_scheme import AuthScheme, AuthSchemeAdmin


class AuthManager:
    def __init__(self, backend: AuthBackend):
        self.backend = backend

        self.auth_scheme = AuthScheme(self.backend)
        self.auth_scheme_admin = AuthSchemeAdmin(self.backend)

        self.current_user = self.auth_scheme
        self.current_user_or_none = self.auth_scheme.current_user_or_none

        self.current_administrator = self.auth_scheme_admin

    async def login(self, id: int, is_admin: bool = False) -> Response:
        return await self.backend.login(id, is_admin)

    async def logout(self) -> Response:
        return await self.backend.logout()
