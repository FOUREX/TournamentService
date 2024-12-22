from pydantic import BaseModel, Field

from src.teams.schemas import STeam

from .enums import ETournamentStatus, ETournamentMemberStatus


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


class STournamentMember(BaseModel):
    team: STeam
    status: ETournamentMemberStatus


class STournament(BaseModel):
    id: int
    name: str = Field(max_length=128)
    description: str | None = Field(max_length=512)
    poster_url: str | None = Field(max_length=256)
    status: ETournamentStatus

    game: SGame
    members: list[STournamentMember]


class STournamentAdd(BaseModel):
    name: str = Field(max_length=128)
    description: str | None = Field(max_length=512)

    game_id: int
