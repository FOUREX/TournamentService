"""Set unique false for MatchMember.match_id

Revision ID: f0c29a645410
Revises: 265a5d7131fd
Create Date: 2024-11-09 07:19:23.482573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0c29a645410'
down_revision: Union[str, None] = '265a5d7131fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
