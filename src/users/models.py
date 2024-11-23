from datetime import datetime

from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import LargeBinary

from src.database import Base


class UserORM(Base):
    __tablename__ = "User"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column((String(length=48)), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column((String(length=48)), nullable=True)
    last_name: Mapped[str] = mapped_column((String(length=48)), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    password: Mapped[bytes] = mapped_column(LargeBinary(length=60))
