from pydantic import BaseModel, ConfigDict

from src.users.schemas import SUser

from .enums import TeamMemberRole


class STeamMember(BaseModel):
    user: SUser
    role: TeamMemberRole


class STeam(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    members: list[STeamMember] = []


class STeamAdd(BaseModel):
    name: str
    members_ids: list[int] = []
