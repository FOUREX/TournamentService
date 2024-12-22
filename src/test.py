import asyncio

from enum import IntEnum
from pprint import pprint

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, ConfigDict

from src.database import async_session_maker
from src.users.models import UserORM
from src.teams.models import TeamORM, TeamMemberORM


class TeamMemberRole(IntEnum):
    owner = 0
    admin = 1
    member = 2
    reserved = 3


class SUser(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime


class SUsers(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    users: list[SUser]


class STeamMember(BaseModel):
    user: SUser
    role: TeamMemberRole


class STeam(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    members: list[STeamMember] | None = None


async def main():
    async with async_session_maker() as session:
        team = (await session.execute(select(TeamORM).options(joinedload(TeamORM.members)))).unique().all()

        print(team[0][0].__dict__)


async def main__():
    _TEAM_ID = 2

    async with async_session_maker() as session:
        teams = (await session.execute(select(TeamORM))).all()
        members = (await session.execute(
            select(TeamMemberORM, UserORM).join(UserORM, UserORM.id == TeamMemberORM.member_id)
        )).all()

    return [
        STeam(
            **team.__dict__,
            members=[
                STeamMember(
                    user=SUser.from_orm(user),
                    role=member.role
                )
                for member, user in members
            ]
        )
        for team in teams
    ]


async def _main():
    _TEAM_ID = 2

    async with async_session_maker() as session:
        team = (await session.execute(
            select(TeamORM).where(TeamORM.id == _TEAM_ID).limit(1)
        )).scalar_one_or_none()

        team_members = (await session.execute(
            select(
                TeamMemberORM, UserORM
            ).join(
                UserORM, UserORM.id == TeamMemberORM.member_id
            ).where(
                TeamMemberORM.team_id == team.team_id
            )
        )).all()

    scheme = STeam(
        **team.__dict__,
        members=[
            STeamMember(
                user=SUser.from_orm(user),
                **member.__dict__
            )
            for member, user in team_members
        ]
    )

    pprint(scheme.dict())


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
