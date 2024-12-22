from sqlalchemy import String, Integer, ForeignKey, URL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.teams.models import TeamORM
from src.database import Base

from .enums import ETournamentStatus, ETournamentMemberStatus


class GameORM(Base):
    __tablename__ = "Game"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column((String(length=64)), unique=True)
    short_name: Mapped[str] = mapped_column((String(length=64)), unique=True)


class TournamentORM(Base):
    __tablename__ = "Tournament"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column((String(length=128)))
    description: Mapped[str] = mapped_column((String(length=512)), nullable=True)
    poster_url: Mapped[str] = mapped_column(String(length=256), nullable=True)
    status: Mapped[ETournamentStatus] = mapped_column(Integer, default=ETournamentStatus.PENDING)

    game_id: Mapped[str] = mapped_column(
        ForeignKey(GameORM.__tablename__ + ".id", ondelete="restrict")
    )

    game: Mapped[GameORM] = relationship()
    members: Mapped[list["TournamentMemberORM"]] = relationship()


class TournamentMemberORM(Base):
    __tablename__ = "TournamentMember"

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey(TournamentORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    team_id: Mapped[TeamORM] = mapped_column(
        ForeignKey(TeamORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )

    status: Mapped[ETournamentMemberStatus] = mapped_column(Integer, default=ETournamentMemberStatus.PENDING)

    team: Mapped[TeamORM] = relationship()



