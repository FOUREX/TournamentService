from abc import ABCMeta, abstractmethod


class BaseStrategy(metaclass=ABCMeta):
    @abstractmethod
    def encode(self, payload: dict) -> str:
        ...

    @abstractmethod
    def decode(self, token: str) -> dict | None:
        ...
