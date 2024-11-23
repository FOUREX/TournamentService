"""Set nullable fo Match.team_winner_id

Revision ID: 265a5d7131fd
Revises: fee3c51c5cd4
Create Date: 2024-11-09 06:48:55.083678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '265a5d7131fd'
down_revision: Union[str, None] = 'fee3c51c5cd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Match', 'team_winner_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Match', 'team_winner_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###