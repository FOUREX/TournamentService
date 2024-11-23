from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import auth_manager
from src.database import get_async_session
from src.users.models import UserORM
from src.teams.schemas import SUser
from src.teams.models import TeamORM, TeamMemberORM
from src.teams.schemas import STeam, STeamMember

from .schemas import SMatchAdd, SMatchEdit, SMatch
from .models import MatchORM, MatchMemberORM
from .enums import MatchType, MatchStatus


match_router = APIRouter(prefix="/match", tags=["Matches"])
matches_router = APIRouter(prefix="/matches", tags=["Matches"])
routers = (match_router, matches_router)


@match_router.get("", response_model=Optional[SMatch])
async def get_match(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        id: int
):
    match = (await session.execute(
        select(
            MatchORM
        ).where(
            MatchORM.id == id
        )
    )).scalar_one_or_none()

    if match is None:
        return None

    teams = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id.in_(
                select(
                    MatchMemberORM.team_id
                ).where(
                    MatchMemberORM.match_id == match.id
                )
            )
        )
    )).scalars().all()

    members = (await session.execute(
        select(TeamMemberORM, UserORM).join(UserORM, UserORM.id == TeamMemberORM.member_id)
    )).all()

    schema = SMatch.from_orm(match)
    schema.members = [
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

    return schema


@match_router.patch("/", response_model=SMatch)
async def edit_match(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        data: SMatchEdit
):
    bad_request_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST
    )

    match = (await session.execute(
        select(
            MatchORM
        ).where(
            MatchORM.id == data.match_id
        )
    )).scalar_one_or_none()

    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with ID {data.match_id} not found"
        )

    match_members_ids = (await session.execute(
        select(
            TeamORM.id
        ).where(
            TeamORM.id.in_(
                select(
                    MatchMemberORM.team_id
                ).where(
                    MatchMemberORM.match_id == match.id
                )
            )
        )
    )).scalars().all()

    if data.status == match.status:
        bad_request_exc.detail = "The match already has this status"
        raise bad_request_exc

    if data.status == MatchStatus.preparing:
        raise bad_request_exc
    elif data.status == MatchStatus.in_progress:
        if match.status != MatchStatus.preparing:
            raise bad_request_exc

        values = {"status": data.status, "started_at": func.now()}
    elif data.status == MatchStatus.finished:
        if match.status != MatchStatus.in_progress:
            raise bad_request_exc
        if data.winner_id is None:
            bad_request_exc.detail = "Winner id is required"
            raise bad_request_exc
        if data.winner_id not in match_members_ids:
            bad_request_exc.detail = f"Team with ID {data.winner_id} does not participate in the match"
            raise bad_request_exc

        values = {"status": data.status, "team_winner_id": data.winner_id, "finished_at": func.now()}
    elif data.status == MatchStatus.cancelled:
        if match.status == MatchStatus.finished:
            raise bad_request_exc

        values = {"status": data.status, "team_winner_id": data.winner_id, "finished_at": func.now()}
    else:
        raise bad_request_exc

    result = (await session.execute(
        update(
            MatchORM
        ).where(
            MatchORM.id == data.match_id
        ).values(
            **values
        ).returning(
            MatchORM
        )
    )).scalar_one()

    await session.commit()

    return result


@match_router.post("/competitive", response_model=SMatch)
async def post_competitive_match(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        data: SMatchAdd
):
    teams_ids = (data.first_team_id, data.second_team_id)

    teams = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id.in_(teams_ids)
        ).limit(2)
    )).scalars().all()

    if len(set(teams)) != 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    match = (await session.execute(
        insert(
            MatchORM
        ).values(
            type=MatchType.competitive
        ).returning(
            MatchORM
        )
    )).scalar_one()

    await session.execute(
        insert(
            MatchMemberORM
        ).values(
            [
                {"match_id": match.id, "team_id": team.id}
                for team in teams
            ]
        )
    )

    schema = SMatch.from_orm(match)

    members = (await session.execute(
        select(TeamMemberORM, UserORM).join(UserORM, UserORM.id == TeamMemberORM.member_id)
    )).all()

    schema.members = [
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

    await session.commit()

    return schema


@matches_router.get("/", response_model=list[SMatch])
async def get_matches(
        session: Annotated[AsyncSession, Depends(get_async_session)],
):
    matches = (await session.execute(
        select(
            MatchORM
        )
    )).scalars().all()

    match_members = (await session.execute(
        select(
            MatchMemberORM
        ).where(
            MatchMemberORM.match_id.in_([match.id for match in matches])
        )
    )).scalars().all()

    teams = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id.in_([match_member.team_id for match_member in match_members])
        )
    )).scalars().all()

    teams_members = (await session.execute(
        select(
            TeamMemberORM, UserORM
        ).join(
            UserORM, UserORM.id == TeamMemberORM.member_id
        ).where(
            TeamMemberORM.team_id.in_([team.id for team in teams])
        )
    )).all()

    return [
        SMatch(
            **match.__dict__,
            members=[
                STeam(
                    **team.__dict__,
                    members=[
                        STeamMember(
                            user=SUser.from_orm(user),
                            role=member.role
                        )
                        for member, user in teams_members if member.team_id == team.id
                    ]
                )
                for team in teams
            ]
        )
        for match in matches
    ]
