from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.teams.schemas import STeam

from .enums import MatchType, MatchStatus


class SMatch(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    type: MatchType
    status: MatchStatus
    members: list[STeam] = []
    winner: STeam | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SMatchMember(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )


class SMatchAdd(BaseModel):
    first_team_id: int
    second_team_id: int


class SMatchEdit(BaseModel):
    match_id: int
    status: MatchStatus
    winner_id: int | None = None
