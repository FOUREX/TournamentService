from pydantic import BaseModel, Field

from src.teams.schemas import STeam

from .enums import ETournamentStatus


class SGame(BaseModel):
    id: int
    name: str = Field(max_length=64)
    short_name: str = Field(max_length=64)


class SGameAdd(BaseModel):
    name: str = Field(max_length=64)
    short_name: str = Field(max_length=64)


class SGameEdit(BaseModel):
    id: int
    name: str = Field(max_length=64)
    short_name: str = Field(max_length=64)


class STournament(BaseModel):
    id: int
    name: str = Field(max_length=128)
    description: str | None = Field(max_length=512)
    avatar_url: str = Field(max_length=256)
    status: ETournamentStatus

    game: SGame
    members: list[STeam]


class STournamentAdd(BaseModel):
    name: str = Field(max_length=128)
    description: str | None = Field(max_length=512)
    game_id: int
