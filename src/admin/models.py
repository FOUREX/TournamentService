from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class AdminORM(Base):
    __tablename__ = "Admin"

    user_id: Mapped[int] = mapped_column(primary_key=True)
