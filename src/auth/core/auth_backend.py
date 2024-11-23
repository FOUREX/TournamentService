from fastapi import Response

from .transport import BaseTransport
from .strategy import BaseStrategy


class AuthBackend:
    def __init__(self, transport: BaseTransport, strategy: BaseStrategy):
        self.transport = transport
        self.strategy = strategy

    async def login(self, user_id: int, is_admin: bool) -> Response:
        token = self.strategy.encode({"id": user_id, "adm": is_admin})

        return self.transport.write_token(token)

    async def logout(self) -> Response:
        return self.transport.delete_token()
