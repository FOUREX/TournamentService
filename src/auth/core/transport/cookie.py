from fastapi import Request, Response, status

from .abc import BaseTransport


class CookieTransport(BaseTransport):
    def __init__(self, cookie_name: str = "access_token", cookie_max_age: int = 3600):
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age

    def get_token(self, request: Request) -> str | None:
        return request.cookies.get(self.cookie_name)

    def write_token(self, token: str) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)

        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.cookie_max_age,
            httponly=True
        )

        return response

    def delete_token(self) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)

        response.set_cookie(
            key=self.cookie_name,
            value="",
            max_age=0
        )

        return response
