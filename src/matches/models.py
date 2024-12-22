from typing import List

from datetime import datetime

from sqlalchemy import ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.teams.models import TeamORM, TeamMemberORM

from .enums import EMatchType, EMatchStatus


class MatchORM(Base):
    __tablename__ = "Match"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EMatchType] = mapped_column(Integer)
    status: Mapped[EMatchStatus] = mapped_column(Integer, default=EMatchStatus.preparing)
    team_winner_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(nullable=True)
    finished_at: Mapped[datetime] = mapped_column(nullable=True)

    members: Mapped[list["MatchMemberORM"]] = relationship()


class MatchMemberORM(Base):
    __tablename__ = "MatchMember"

    match_id: Mapped[int] = mapped_column(
        ForeignKey(MatchORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    team: Mapped[TeamORM] = relationship()
    stack: Mapped[list["TeamMemberORM"]] = relationship(secondary="MatchStack")


class MatchStackORM(Base):
    __tablename__ = "MatchStack"

    match_id: Mapped[int] = mapped_column(
        ForeignKey(MatchORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    member_id: Mapped[int] = mapped_column(primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["team_id", "member_id"],
            [TeamMemberORM.__tablename__ + ".team_id", TeamMemberORM.__tablename__ + ".member_id"]
        ),
        ForeignKeyConstraint(
            ["match_id", "team_id"],
            [MatchMemberORM.__tablename__ + ".match_id", MatchMemberORM.__tablename__ + ".team_id"]
        ),
        PrimaryKeyConstraint("match_id", "team_id", "member_id")
    )  # Sell my soul

    # member: Mapped[TeamMemberORM] = relationship(overlaps="stack")
