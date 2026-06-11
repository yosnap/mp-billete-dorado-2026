"""add audit_seed to prize_assignments

Revision ID: prizes_0004
Revises: prizes_0003
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "prizes_0004"
down_revision: Union[str, None] = "prizes_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Valor del random usado en el spin — permite reproducir y auditar el resultado
    op.add_column(
        "prize_assignments",
        sa.Column("audit_seed", sa.Numeric(precision=20, scale=18), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("prize_assignments", "audit_seed")
