from pydantic import BaseModel, Field


class SUserRegister(BaseModel):
    name: str = Field(max_length=48, pattern="([A-Za-z0-9_]+)")
    password: str = Field(max_length=128)


class SUserLogin(BaseModel):
    name: str = Field(max_length=48, pattern="([A-Za-z0-9_]+)")
    password: str = Field(max_length=128)
