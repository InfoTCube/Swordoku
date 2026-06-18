"""add game settings to lobbies and matches

Revision ID: a1b2c3d4e5f6
Revises: 96fc2f278240
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '96fc2f278240'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lobbies', sa.Column('time_limit_min', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('lobbies', sa.Column('mistake_limit', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('matches', sa.Column('time_limit_s', sa.Integer(), nullable=False, server_default='600'))
    op.add_column('matches', sa.Column('mistake_limit', sa.Integer(), nullable=False, server_default='3'))


def downgrade() -> None:
    op.drop_column('matches', 'mistake_limit')
    op.drop_column('matches', 'time_limit_s')
    op.drop_column('lobbies', 'mistake_limit')
    op.drop_column('lobbies', 'time_limit_min')
