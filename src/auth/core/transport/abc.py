from abc import ABCMeta, abstractmethod

from fastapi import Request, Response


class BaseTransport(metaclass=ABCMeta):
    @abstractmethod
    def get_token(self, request: Request) -> str | None:
        ...

    @abstractmethod
    def write_token(self, token: str) -> Response:
        ...

    @abstractmethod
    def delete_token(self) -> Response:
        ...
