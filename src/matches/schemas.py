from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.teams.schemas import STeam, STeamMember

from .enums import EMatchType, EMatchStatus


class SMatchMember(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    team: STeam
    stack: list[STeamMember]


class SMatch(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    type: EMatchType
    status: EMatchStatus
    members: list[SMatchMember] = []
    winner: STeam | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SMatchAdd(BaseModel):
    first_team_id: int
    second_team_id: int


class SMatchEdit(BaseModel):
    match_id: int
    status: EMatchStatus
    winner_id: int | None = None
