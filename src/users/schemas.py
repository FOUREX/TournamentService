from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SPersonalData(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    first_name: str | None = None
    last_name: str | None = None


class SUser(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    personal_data: SPersonalData = SPersonalData()
    created_at: datetime
