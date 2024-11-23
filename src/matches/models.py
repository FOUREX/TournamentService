from datetime import datetime

from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.teams.models import TeamORM

from .enums import MatchType, MatchStatus


class MatchORM(Base):
    __tablename__ = "Match"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[MatchType] = mapped_column(Integer)
    status: Mapped[MatchStatus] = mapped_column(Integer, default=MatchStatus.preparing)
    team_winner_id: Mapped[int] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(nullable=True)
    finished_at: Mapped[datetime] = mapped_column(nullable=True)


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
