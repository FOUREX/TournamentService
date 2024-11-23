"""Initial

Revision ID: 721685dbd7c1
Revises: 78a90df545e1
Create Date: 2024-10-27 17:05:49.742732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '721685dbd7c1'
down_revision: Union[str, None] = '78a90df545e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
