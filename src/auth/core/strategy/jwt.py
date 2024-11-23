import jwt

from .abc import BaseStrategy


class JWTStrategy(BaseStrategy):
    def __init__(self, secret: str, algorithms: list[str] = None):
        self.secret = secret
        self.algorithms = ["HS256"] if algorithms is None else algorithms

    def encode(self, payload: dict) -> str:
        return jwt.encode(
            payload=payload,
            key=self.secret,
            algorithm=self.algorithms[0]
        )

    def decode(self, token: str) -> dict | None:
        return jwt.decode(
            jwt=token,
            key=self.secret,
            algorithms=self.algorithms
        )
