"""Add users

Revision ID: b30dbd404126
Revises: 2c3205e1cf49
Create Date: 2024-10-30 16:53:05.196065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b30dbd404126'
down_revision: Union[str, None] = '2c3205e1cf49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=48), nullable=False),
    sa.Column('first_name', sa.String(length=48), nullable=False),
    sa.Column('second_name', sa.String(length=48), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('TeamsMembers',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('member_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['Teams.id'], ),
    sa.PrimaryKeyConstraint('team_id', 'member_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('TeamsMembers')
    op.drop_table('Users')
    # ### end Alembic commands ###
