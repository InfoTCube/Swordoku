"""fix board_state empty default

Revision ID: d4e5f6a1b2c3
Revises: a1b2c3d4e5f6
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ZERO_BOARD = '[' + ','.join(['0'] * 81) + ']'


def upgrade() -> None:
    # Rows inserted by the migration that added the board_state column received
    # server_default='[]' (an empty array) instead of the ORM-level default of
    # [0]*81.  An empty board causes IndexError when a move is processed, so
    # backfill any such rows here.
    op.execute(
        sa.text(
            "UPDATE match_participants SET board_state = :zero WHERE board_state = '[]'"
        ).bindparams(zero=_ZERO_BOARD)
    )


def downgrade() -> None:
    pass
