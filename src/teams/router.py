from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth import auth_manager
from src.users.models import UserORM
from src.users.schemas import SUser

from .models import TeamORM, TeamMemberORM
from .schemas import STeam, STeamAdd, STeamMember
from .enums import TeamMemberRole


team_router = APIRouter(prefix="/team", tags=["Teams"])
teams_router = APIRouter(prefix="/teams", tags=["Teams"])

routers = (team_router, teams_router)


@team_router.get("/", response_model=Optional[STeam])
async def get_team(session: Annotated[AsyncSession, Depends(get_async_session)],
                   id: int | None = None, name: str | None = None):
    if id is not None:
        query = select(TeamORM).where(TeamORM.id == id).limit(1)
    elif name is not None:
        query = select(TeamORM).where(TeamORM.name.ilike(name)).limit(1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An ID or name is required"
        )

    team = (await session.execute(query)).scalar_one_or_none()

    if team is None:
        return None

    team_members = (await session.execute(
        select(
            TeamMemberORM, UserORM
        ).join(
            UserORM, UserORM.id == TeamMemberORM.member_id
        ).where(
            TeamMemberORM.team_id == team.id
        )
    )).all()

    schema = STeam(
        **team.__dict__,
        members=[
            STeamMember(
                user=SUser.from_orm(user),
                **member.__dict__
            )
            for member, user in team_members
        ]
    )

    return schema


@team_router.post("/", response_model=STeam)
async def post_team(session: Annotated[AsyncSession, Depends(get_async_session)],
                    current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
                    team: STeamAdd):
    query = select(TeamORM).where(TeamORM.name.ilike(team.name))

    if (await session.execute(query)).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team with this name already exists"
        )

    created_team_id = (await session.execute(
        insert(
            TeamORM
        ).values(
            team.dict(include=set(TeamORM.__dict__.keys()))
        ).returning(TeamORM.id)
    )).scalar_one()

    # TODO: Add members from team.members_ids

    await session.execute(
        insert(TeamMemberORM).values(team_id=created_team_id, member_id=current_user.id, role=TeamMemberRole.owner)
    )

    await session.commit()

    return await get_team(session, created_team_id)


@team_router.post("/member", response_model=STeamMember)  # TODO: Тільки власник може додавати адмінів
async def post_team_member(session: Annotated[AsyncSession, Depends(get_async_session)],
                           current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
                           team_id: int, user_id: int, role: int = TeamMemberRole.member):
    team = (await session.execute(
        select(TeamORM).where(TeamORM.id == team_id).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    team_administrators_ids, team_administrators_roles = zip(*(await session.execute(
        select(TeamMemberORM.member_id, TeamMemberORM.role).where(
            TeamMemberORM.team_id == team_id, TeamMemberORM.role <= TeamMemberRole.admin
        )
    )).all())

    if current_user.id not in team_administrators_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator can add members to a team"
        )

    if (
        role <= TeamMemberRole.admin and
        team_administrators_roles[team_administrators_ids.index(current_user.id)] != TeamMemberRole.owner
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can add an administrator to the team"
        )

    if role == TeamMemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team cannot have more than one owner"
        )

    if role not in TeamMemberRole.__members__.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    user = (await session.execute(
        select(UserORM).where(UserORM.id == user_id).limit(1)
    )).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist"
        )

    member = (await session.execute(
        select(TeamMemberORM).where(TeamMemberORM.team_id == team.id, TeamMemberORM.member_id == user.id).limit(1)
    )).scalar_one_or_none()

    if member is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID {user_id} is a member of team with ID {team_id}"
        )

    member = (await session.execute(
        insert(
            TeamMemberORM
        ).values(
            team_id=team.id, member_id=user.id, role=role
        ).returning(
            TeamMemberORM
        )
    )).scalar_one()

    await session.commit()

    return STeamMember(
        user=user,
        role=member.role
    )


@team_router.post("/members")
async def post_team_members(session: Annotated[AsyncSession, Depends(get_async_session)],
                            current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
                            team_id: int, user_ids: list[int]):
    ...


@teams_router.get("/", response_model=list[STeam])  # TODO: Зробить нормально; маладец, зробив
async def get_teams(session: Annotated[AsyncSession, Depends(get_async_session)]):
    teams = (await session.execute(select(TeamORM))).scalars().all()
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
                for member, user in members if member.team_id == team.id
            ]
        )
        for team in teams
    ]
