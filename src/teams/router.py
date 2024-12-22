from typing import Optional, Annotated, Sequence

from fastapi import APIRouter, Depends, Body, Response, HTTPException, status
from sqlalchemy import select, insert, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth import auth_manager
from src.users.models import UserORM

from .models import TeamORM, TeamMemberORM, TeamJoinRequestORM
from .schemas import STeam, STeamAdd, STeamMember, FTeamID, STeamRequest, STeamInvitation
from .enums import ETeamMemberRole, ETeamJoinRequestType


team_router = APIRouter(prefix="/team", tags=["Teams"])
teams_router = APIRouter(prefix="/teams", tags=["Teams"])
member_router = APIRouter(prefix="/team/member", tags=["Teams"])
join_router = APIRouter(prefix="/team/join", tags=["Teams"])

routers = (team_router, member_router, join_router, teams_router)


@team_router.get("/", response_model=Optional[STeam])
async def get_team(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        id: int | None = None, name: str | None = None
):
    if id is not None:
        params = TeamORM.id == id
    elif name is not None:
        params = TeamORM.name.ilike(name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An ID or name is required"
        )

    team = (await session.execute(
        select(
            TeamORM
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
        ).where(
            params
        )
    )).unique().scalar_one_or_none()

    if team is None:
        return None

    return team


@team_router.post("/", response_model=STeam)
async def post_team(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team: STeamAdd
):
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
        insert(TeamMemberORM).values(team_id=created_team_id, member_id=current_user.id, role=ETeamMemberRole.OWNER)
    )

    await session.commit()

    return await get_team(session, created_team_id)


@join_router.post("/invite", description="Send an invitation to the team")
async def post_join_invite(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: Annotated[int, Body()], user_id: Annotated[int, Body()]
):
    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    team_administrators_ids, team_administrators_roles = zip(*(await session.execute(
        select(TeamMemberORM.member_id, TeamMemberORM.role).where(
            TeamMemberORM.team_id == team_id, TeamMemberORM.role <= ETeamMemberRole.ADMIN
        )
    )).all())

    if current_user.id not in team_administrators_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator can send invitations to the team"
        )

    user = (await session.execute(
        select(
            UserORM
        ).where(
            UserORM.id == user_id
        ).limit(1)
    )).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist"
        )

    member = (await session.execute(
        select(
            TeamMemberORM
        ).where(
            TeamMemberORM.team_id == team.id,
            TeamMemberORM.member_id == user.id
        ).limit(1)
    )).scalar_one_or_none()

    if member is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID {user_id} is a member of team with ID {team_id}"
        )

    request = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id
        ).limit(1)
    )).scalar_one_or_none()

    if request is not None:
        details = (
            "The invitation is already waiting for user approval",
            "A request from this user is already pending approval"
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=details[request.type]
        )

    await session.execute(
        insert(
            TeamJoinRequestORM
        ).values(
            team_id=team_id,
            user_id=user_id,
            type=ETeamJoinRequestType.INVITE
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.patch("/invite", description="Accept an invitation to the team")
async def patch_join_invite(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: FTeamID
):
    team_id = team_id.team_id

    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    invite = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == current_user.id,
            TeamJoinRequestORM.type == ETeamJoinRequestType.INVITE
        ).limit(1)
    )).scalar_one_or_none()

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation does not exist"
        )

    await session.execute(
        delete(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == current_user.id
        )
    )

    await session.execute(
        insert(
            TeamMemberORM
        ).values(
            team_id=team.id,
            member_id=current_user.id
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.delete("/invite", description="Delete an invitation to the team")
async def delete_join_invite(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: Annotated[int, Body()], user_id: Annotated[int | None, Body()] = None
):
    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    if user_id is not None:
        team_administrators_ids, team_administrators_roles = zip(*(await session.execute(
            select(TeamMemberORM.member_id, TeamMemberORM.role).where(
                TeamMemberORM.team_id == team_id, TeamMemberORM.role <= ETeamMemberRole.ADMIN
            )
        )).all())

        if current_user.id not in team_administrators_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an administrator can cancel an invitation to a team"
            )
    else:
        user_id = current_user.id

    invite = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id,
            TeamJoinRequestORM.type == ETeamJoinRequestType.INVITE
        ).limit(1)
    )).scalar_one_or_none()

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation does not exist"
        )

    await session.execute(
        delete(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.post("/request", description="Send a request to the team")
async def post_join_request(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: FTeamID
):
    team_id = team_id.team_id

    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    member = (await session.execute(
        select(
            TeamMemberORM
        ).where(
            TeamMemberORM.team_id == team.id,
            TeamMemberORM.member_id == current_user.id
        ).limit(1)
    )).scalar_one_or_none()

    if member is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID {current_user.id} is a member of team with ID {team_id}"
        )

    request = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == current_user.id
        ).limit(1)
    )).scalar_one_or_none()

    if request is not None:
        details = (
            "The invitation is already waiting for user approval",
            "A request from this user is already pending approval"
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=details[request.type]
        )

    await session.execute(
        insert(
            TeamJoinRequestORM
        ).values(
            team_id=team_id,
            user_id=current_user.id,
            type=ETeamJoinRequestType.REQUEST
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.patch("/request", description="Patch a request to the team")
async def patch_join_request(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: Annotated[int, Body()], user_id: Annotated[int, Body()]
):
    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    team_administrators_ids, team_administrators_roles = zip(*(await session.execute(
        select(TeamMemberORM.member_id, TeamMemberORM.role).where(
            TeamMemberORM.team_id == team_id, TeamMemberORM.role <= ETeamMemberRole.ADMIN
        )
    )).all())

    if current_user.id not in team_administrators_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the administrator can accept requests to join the team"
        )

    request = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id,
            TeamJoinRequestORM.type == ETeamJoinRequestType.REQUEST
        ).limit(1)
    )).scalar_one_or_none()

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The request does not exist"
        )

    await session.execute(
        delete(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id
        )
    )

    await session.execute(
        insert(
            TeamMemberORM
        ).values(
            team_id=team.id,
            member_id=user_id
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.delete("/request", description="Reject a request to the team")
async def delete_join_request(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)],
        team_id: Annotated[int, Body()], user_id: Annotated[int, Body()]
):
    team = (await session.execute(
        select(
            TeamORM
        ).where(
            TeamORM.id == team_id
        ).limit(1)
    )).scalar_one_or_none()

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with ID {team_id} does not exist"
        )

    team_administrators_ids, team_administrators_roles = zip(*(await session.execute(
        select(TeamMemberORM.member_id, TeamMemberORM.role).where(
            TeamMemberORM.team_id == team_id, TeamMemberORM.role <= ETeamMemberRole.ADMIN
        )
    )).all())

    if current_user.id not in team_administrators_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the administrator can reject requests to join the team"
        )

    request = (await session.execute(
        select(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id,
            TeamJoinRequestORM.type == ETeamJoinRequestType.REQUEST
        ).limit(1)
    )).scalar_one_or_none()

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The request does not exist"
        )

    await session.execute(
        delete(
            TeamJoinRequestORM
        ).where(
            TeamJoinRequestORM.team_id == team_id,
            TeamJoinRequestORM.user_id == user_id
        )
    )

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@join_router.get("/invitations", description="Gen invitations of current user")
async def get_invitations(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)]
) -> Sequence[STeamInvitation]:
    return (await session.execute(
        select(
            TeamJoinRequestORM
        ).options(
            joinedload(
                TeamJoinRequestORM.team
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
        ).where(
            TeamJoinRequestORM.user_id == current_user.id,
            TeamJoinRequestORM.type == ETeamJoinRequestType.INVITE
        )
    )).unique().scalars().all()


@team_router.post("/member", response_model=STeamMember)  # TODO: Тільки власник може додавати адмінів
async def post_team_member(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_administrator)],
        team_id: int, user_id: int, role: int = ETeamMemberRole.MEMBER
):
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
            TeamMemberORM.team_id == team_id, TeamMemberORM.role <= ETeamMemberRole.ADMIN
        )
    )).all())

    if current_user.id not in team_administrators_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator can add members to a team"
        )

    if (
        role <= ETeamMemberRole.ADMIN and
        team_administrators_roles[team_administrators_ids.index(current_user.id)] != ETeamMemberRole.OWNER
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can add an administrator to the team"
        )

    if role == ETeamMemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team cannot have more than one owner"
        )

    if role not in ETeamMemberRole.__members__.values():
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


@teams_router.get("/", response_model=list[STeam])  # TODO: Зробить нормально; маладец, зробив; маладец, зробив х2
async def get_teams(
        session: Annotated[AsyncSession, Depends(get_async_session)]
):
    members = (await session.execute(
        select(
            TeamORM
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
    )).unique().scalars().all()

    return members


@teams_router.get("/my")
async def get_my_teams(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: Annotated[UserORM, Depends(auth_manager.current_user)]
) -> Sequence[STeam]:
    return (await session.execute(
        select(
            TeamORM
        ).join(
            TeamMemberORM
        ).where(
            TeamMemberORM.member_id == current_user.id,
            TeamMemberORM.role == ETeamMemberRole.OWNER
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
    )).unique().scalars().all()
