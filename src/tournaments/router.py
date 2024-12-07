from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Body, Query, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth import auth_manager
from src.users.models import UserORM
from src.teams.models import TeamORM, TeamMemberORM

from .models import TournamentORM, GameORM
from .schemas import STournament, SGame, SGameAdd, SGameEdit

tournament_router = APIRouter(prefix="/tournament", tags=["Tournament"])
tournaments_router = APIRouter(prefix="/tournaments", tags=["Tournament"])

game_router = APIRouter(prefix=tournament_router.prefix + "/game", tags=["Tournament"])
games_router = APIRouter(prefix=tournament_router.prefix + "/games", tags=["Tournament"])

routers = (tournament_router, tournaments_router, game_router, games_router)


@tournament_router.get("/")
async def get_tournament(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        id: Annotated[int, Query()]
) -> STournament | None:
    return (await session.execute(
        select(
            TournamentORM
        ).options(
            joinedload(
                TournamentORM.game
            ),
            joinedload(
                TournamentORM.members
            ).joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            )
        ).where(
            TournamentORM.id == id
        ).limit(1)
    )).unique().scalar_one_or_none()


@tournament_router.post("/")
async def post_tournament(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)]
) -> STournament:
    ...


@tournaments_router.get("/")
async def get_tournaments(

) -> list[STournament]:
    ...


@game_router.get("/")
async def get_game(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        id: Annotated[int, Query()]
) -> SGame | None:
    return (await session.execute(
        select(
            GameORM
        ).where(
            GameORM.id == id
        )
    )).scalar_one_or_none()


@game_router.post("/")
async def post_game(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        game: Annotated[SGameAdd, Body()]
) -> SGame:
    name_is_used = (await session.execute(
        select(
            GameORM
        ).where(
            GameORM.name.ilike(game.name)
        ).limit(1)
    )).scalar_one_or_none() is not None

    short_name_is_used = (await session.execute(
        select(
            GameORM
        ).where(
            GameORM.short_name.ilike(game.short_name)
        ).limit(1)
    )).scalar_one_or_none() is not None

    if name_is_used:
        raise HTTPException(
            detail="Name is used",
            status_code=status.HTTP_409_CONFLICT
        )

    if short_name_is_used:
        raise HTTPException(
            detail="Short name is used",
            status_code=status.HTTP_409_CONFLICT
        )

    result = (await session.execute(
        insert(
            GameORM
        ).values(
            game.dict()
        ).returning(
            GameORM
        )
    )).scalar_one()

    await session.commit()

    return result


@game_router.put("/")
async def put_game(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        game: Annotated[SGameEdit, Body()]
) -> SGame:
    ...


@games_router.get("/")
async def get_games(
        session: Annotated[AsyncSession, Depends(get_async_session)],

) -> Sequence[SGame]:
    return (await session.execute(
        select(
            GameORM
        )
    )).scalars().all()
