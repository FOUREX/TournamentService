from io import BytesIO
from time import time
from typing import Annotated, Sequence

from fastapi import (APIRouter, Depends, Body, Query, Form, UploadFile,
                     File, Response, HTTPException, status as http_status)
from sqlalchemy import insert, select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image, UnidentifiedImageError

from src.database import get_async_session
from src.auth import auth_manager
from src.users.models import UserORM
from src.teams.models import TeamORM, TeamMemberORM, TeamJoinRequestORM
from src.teams.enums import ETeamMemberRole
from src.s3client import s3_client as s3client

from .models import TournamentORM, TournamentMemberORM, GameORM
from .schemas import STournament, SGame, SGameAdd, SGameEdit, STournamentAdd
from .enums import ETournamentStatus, ETournamentMemberStatus


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
                TournamentMemberORM.team
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
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        name: Annotated[str, Form(max_length=128)],
        description: Annotated[str, Form(max_length=512)],
        game_id: Annotated[int, Form()],
        poster: Annotated[UploadFile, File()]
) -> STournament:
    tournament = STournamentAdd(
        name=name,
        description=description,
        game_id=game_id
    )

    poster = await poster.read()

    try:
        image = Image.open(BytesIO(poster))

        if image.format.upper() not in ["PNG", "JPG", "JPEG", "WEBP"]:
            raise HTTPException(
                detail="Invalid image format. Allowed: PNG, JPG, JPEG, WEBP",
                status_code=http_status.HTTP_400_BAD_REQUEST
            )
    except UnidentifiedImageError:
        raise HTTPException(
            detail="Invalid image",
            status_code=http_status.HTTP_400_BAD_REQUEST
        )

    object_name = f"TO_{int(time())}_poster.{image.format.lower()}"

    response_id = (await session.execute(
        insert(
            TournamentORM
        ).values(
            name=tournament.name,
            description=tournament.description,
            game_id=tournament.game_id,
            poster_url=s3client.gen_url(object_name)
        ).returning(
            TournamentORM.id
        )
    )).scalar_one()

    await s3client.upload_file(poster, object_name)

    await session.commit()

    return (await session.execute(
        select(
            TournamentORM
        ).options(
            joinedload(
                TournamentORM.game
            ),
            joinedload(
                TournamentORM.members
            )
        ).where(
            TournamentORM.id == response_id
        ).limit(1)
    )).unique().scalar_one()


@tournament_router.post("/member")
async def post_tournament_member(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        user: Annotated[UserORM, Depends(auth_manager.current_user)],
        tournament_id: Annotated[int, Body()],
        team_id: Annotated[int, Body()]
):
    tournament = (await session.execute(
        select(
            TournamentORM
        ).options(
            joinedload(
                TournamentORM.game
            ),
            joinedload(
                TournamentORM.members
            ).joinedload(
                TournamentMemberORM.team
            )
        ).where(
            TournamentORM.id == tournament_id
        ).limit(1)
    )).unique().scalar_one_or_none()

    if tournament is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with ID {tournament_id} does not exist"
        )

    if tournament.status != ETournamentStatus.PENDING:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=f"It is no longer possible to join a tournament with ID {tournament_id}"
        )

    team = (await session.execute(
        select(
            TeamORM
        ).options(
            joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            )
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).unique().scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    user_role = {member.user.id: member.role for member in team.members}.get(user.id)

    if user_role is None or not user_role <= ETeamMemberRole.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only the administrator can send requests to participate in tournaments"
        )

    tournament_member_status = {member.team.id: member.status for member in tournament.members}.get(team_id)

    if tournament_member_status == ETournamentMemberStatus.ACCEPTED:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Team with ID {team_id} is already a participant in tournament with ID {tournament_id}"
        )

    if tournament_member_status == ETournamentMemberStatus.PENDING:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Team with ID {team_id} is already waiting to participate in the tournament with ID {tournament_id}"
        )

    await session.execute(
        insert(
            TournamentMemberORM
        ).values(
            tournament_id=tournament_id,
            team_id=team_id
        )
    )

    await session.commit()

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@tournament_router.patch("/member")
async def patch_tournament_member(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        _: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        tournament_id: Annotated[int, Body()],
        team_id: Annotated[int, Body()],
        status: Annotated[ETournamentMemberStatus, Body()],
):
    tournament = (await session.execute(
        select(
            TournamentORM
        ).options(
            joinedload(
                TournamentORM.game
            ),
            joinedload(
                TournamentORM.members
            ).joinedload(
                TournamentMemberORM.team
            )
        ).where(
            TournamentORM.id == tournament_id
        ).limit(1)
    )).unique().scalar_one_or_none()

    if tournament is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with ID {tournament_id} does not exist"
        )

    team = (await session.execute(
        select(
            TeamORM
        ).options(
            joinedload(
                TeamORM.members
            ).joinedload(
                TeamMemberORM.user
            )
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).unique().scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    tournament_member_status = {member.team.team_id: member.status for member in tournament.members}.get(team_id)

    if tournament_member_status is None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Team with ID {team_id} does not a participate in tournament with ID {tournament_id}"
        )

    await session.execute(
        update(
            TournamentMemberORM
        ).where(
            TournamentMemberORM.tournament_id == tournament_id,
            TournamentMemberORM.team_id == team_id
        ).values(
            status=status
        )
    )

    await session.commit()

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@tournaments_router.get("/")
async def get_tournaments(
        session: Annotated[AsyncSession, Depends(get_async_session)]
) -> Sequence[STournament]:
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
                TournamentMemberORM.team
            ).options(
                joinedload(
                    TeamORM.members
                ).joinedload(
                    TeamMemberORM.user
                ),
                joinedload(
                    TeamORM.join_requests
                ).joinedload(
                    TeamJoinRequestORM.user
                )
            )
        )
    )).unique().scalars().all()


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
            status_code=http_status.HTTP_409_CONFLICT
        )

    if short_name_is_used:
        raise HTTPException(
            detail="Short name is used",
            status_code=http_status.HTTP_409_CONFLICT
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
