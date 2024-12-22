from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select, update, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import auth_manager
from src.database import get_async_session
from src.users.models import UserORM
from src.teams.models import TeamORM, TeamMemberORM

from .schemas import SMatchAdd, SMatchEdit, SMatch
from .models import MatchORM, MatchMemberORM
from .enums import EMatchType, EMatchStatus


match_router = APIRouter(prefix="/match", tags=["Matches"])
matches_router = APIRouter(prefix="/matches", tags=["Matches"])
routers = (match_router, matches_router)


@match_router.get("/", response_model=Optional[SMatch])
async def get_match(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        id: int
):
    return (await session.execute(
        select(
            MatchORM
        ).options(
            joinedload(
                MatchORM.members
            ).joinedload(
                MatchMemberORM.team
            ).joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            ),
            joinedload(
                MatchORM.members
            ).joinedload(
                MatchMemberORM.stack
            ).joinedload(
                TeamMemberORM.user
            )
        ).where(
            MatchORM.id == id
        ).limit(1)
    )).unique().scalar_one_or_none()


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

    if data.status == EMatchStatus.preparing:
        raise bad_request_exc
    elif data.status == EMatchStatus.in_progress:
        if match.status != EMatchStatus.preparing:
            raise bad_request_exc

        values = {"status": data.status, "started_at": func.now()}
    elif data.status == EMatchStatus.finished:
        if match.status != EMatchStatus.in_progress:
            raise bad_request_exc
        if data.winner_id is None:
            bad_request_exc.detail = "Winner id is required"
            raise bad_request_exc
        if data.winner_id not in match_members_ids:
            bad_request_exc.detail = f"Team with ID {data.winner_id} does not participate in the match"
            raise bad_request_exc

        values = {"status": data.status, "team_winner_id": data.winner_id, "finished_at": func.now()}
    elif data.status == EMatchStatus.cancelled:
        if match.status == EMatchStatus.finished:
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
            type=EMatchType.competitive
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

    await session.commit()

    r = (await session.execute(
        select(
            MatchORM
        ).options(
            joinedload(
                MatchORM.members
            ).joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            )
        ).where(
            MatchORM.id == match.id
        ).limit(1)
    )).unique().scalar_one_or_none()

    return r


@matches_router.get("/", response_model=list[SMatch])
async def get_matches(
        session: Annotated[AsyncSession, Depends(get_async_session)],
):
    return (await session.execute(
        select(
            MatchORM
        ).options(
            joinedload(
                MatchORM.members
            ).joinedload(
                MatchMemberORM.team
            ).joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            )
        )
    )).unique().scalars().all()
