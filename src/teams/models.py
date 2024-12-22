from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.users.models import UserORM
from src.database import Base

from .enums import ETeamMemberRole, ETeamJoinRequestType


class TeamORM(Base):
    __tablename__ = "Team"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column((String(length=48)))
    avatar_url: Mapped[str] = mapped_column((String(length=256)), nullable=True)

    members: Mapped[list["TeamMemberORM"]] = relationship()
    join_requests: Mapped[list["TeamJoinRequestORM"]] = relationship()


class TeamMemberORM(Base):
    __tablename__ = "TeamMember"

    team_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey(UserORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    role: Mapped[ETeamMemberRole] = mapped_column(Integer, default=ETeamMemberRole.MEMBER)
    user: Mapped[UserORM] = relationship()


class TeamJoinRequestORM(Base):
    __tablename__ = "TeamJoinRequest"

    team_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(UserORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    type: Mapped[ETeamJoinRequestType] = mapped_column(Integer)
    user: Mapped[UserORM] = relationship()
    team: Mapped[TeamORM] = relationship(viewonly=True)
