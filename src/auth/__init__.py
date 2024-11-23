from src.config import JWT_SECRET

from .core.auth_manager import AuthManager
from .core.auth_backend import AuthBackend
from .core.transport import CookieTransport
from .core.strategy import JWTStrategy


auth_manager = AuthManager(
    AuthBackend(
        CookieTransport(),
        JWTStrategy(JWT_SECRET)
    )
)
