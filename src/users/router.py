from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.teams.schemas import STeam, STeamMember
from src.teams.models import TeamORM, TeamMemberORM
from src.database import get_async_session
from src.auth import auth_manager

from .models import UserORM
from .schemas import SUser, SPersonalData


user_router = APIRouter(prefix="/user", tags=["Users"])
users_router = APIRouter(prefix="/users", tags=["Users"])
current_user_router = APIRouter(prefix="/me", tags=["Users"])

routers = (user_router, users_router, current_user_router)


@user_router.get("/", response_model=SUser | None)
async def get_user(session: Annotated[AsyncSession, Depends(get_async_session)],
                   current_user: Annotated[UserORM, Depends(auth_manager.current_user_or_none)],
                   id: int | None = None, name: str | None = None):
    if id is not None:
        query = select(UserORM).where(UserORM.id == id).limit(1)
    elif name is not None:
        query = select(UserORM).where(UserORM.name.ilike(name)).limit(1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An ID or name is required"
        )

    response = (await session.execute(query)).scalar_one_or_none()

    if response is None:
        return None

    user = SUser.from_orm(response)

    if current_user is not None and current_user.id == user.id:
        user.personal_data = SPersonalData.from_orm(response)

    return user


@users_router.get("/", response_model=list[SUser])
async def get_users(session: Annotated[AsyncSession, Depends(get_async_session)]):
    return (await session.execute(select(UserORM))).scalars().all()


@current_user_router.get("/", response_model=SUser)
async def get_current_user(current_user: Annotated[UserORM, Depends(auth_manager.current_user)]):
    schema = SUser.from_orm(current_user)
    schema.personal_data = SPersonalData.from_orm(current_user)

    return schema


@current_user_router.get("/teams", response_model=list[STeam])
async def get_current_user_teams(session: Annotated[AsyncSession, Depends(get_async_session)],
                                 current_user: Annotated[UserORM, Depends(auth_manager.current_user)]):
    teams = (await session.execute(
        select(TeamORM).where(TeamORM.id.in_(
            select(TeamMemberORM.team_id).where(TeamMemberORM.member_id == current_user.id)
        ))
    )).scalars().all()

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
