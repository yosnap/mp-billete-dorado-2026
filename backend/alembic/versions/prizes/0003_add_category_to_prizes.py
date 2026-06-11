"""add category column to prizes

Revision ID: prizes_0003
Revises: prizes_0002
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "prizes_0003"
down_revision: Union[str, None] = "prizes_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prizes",
        sa.Column(
            "category",
            sa.String(20),
            nullable=False,
            server_default="small",
        ),
    )
    op.alter_column("prizes", "category", server_default=None)


def downgrade() -> None:
    op.drop_column("prizes", "category")
