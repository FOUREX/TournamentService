from pydantic import BaseModel, ConfigDict

from src.users.schemas import SUser

from .enums import ETeamMemberRole, ETeamJoinRequestType


class FTeamID(BaseModel):
    team_id: int


class STeamMember(BaseModel):
    user: SUser
    role: ETeamMemberRole


class STeamRequest(BaseModel):
    user: SUser
    type: ETeamJoinRequestType


class STeam(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    avatar_url: str | None

    members: list[STeamMember] = []
    join_requests: list[STeamRequest] = []


class STeamInvitation(BaseModel):
    team: STeam
    type: ETeamJoinRequestType


class STeamAdd(BaseModel):
    name: str
    members_ids: list[int] = []
