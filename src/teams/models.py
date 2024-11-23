from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.users.models import UserORM
from src.database import Base

from .enums import TeamMemberRole


class TeamORM(Base):
    __tablename__ = "Team"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column((String(length=48)))

    members: Mapped[list["TeamMemberORM"]] = relationship("TeamMemberORM", back_populates="team")


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

    role: Mapped[TeamMemberRole] = mapped_column(Integer, default=TeamMemberRole.member)

    team: Mapped["TeamORM"] = relationship("TeamORM", back_populates="members")
