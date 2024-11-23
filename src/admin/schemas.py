from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.users.models import UserORM


class AdminORM(Base):
    __tablename__ = "Admin"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(UserORM.__tablename__ + ".id", ondelete="cascade"),
        primary_key=True
    )
