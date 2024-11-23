"""Wtf x2 rollback

Revision ID: 83e449319632
Revises: 0dbb99c94030
Create Date: 2024-11-09 10:09:39.634182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83e449319632'
down_revision: Union[str, None] = '0dbb99c94030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Match',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('team_winner_id', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['team_winner_id'], ['Team.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('MatchMember',
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['Match.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['team_id'], ['Team.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('match_id', 'team_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('MatchMember')
    op.drop_table('Match')
    # ### end Alembic commands ###
