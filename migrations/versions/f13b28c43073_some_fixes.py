"""Some fixes

Revision ID: f13b28c43073
Revises: 9091df2993b1
Create Date: 2024-10-30 18:59:24.124254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f13b28c43073'
down_revision: Union[str, None] = '9091df2993b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('last_name', sa.String(length=48), nullable=False))
    op.drop_column('Users', 'second_name')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('second_name', sa.VARCHAR(length=48), autoincrement=False, nullable=False))
    op.drop_column('Users', 'last_name')
    # ### end Alembic commands ###
