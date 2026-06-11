"""create prize_assignments table

Revision ID: prizes_0002
Revises: prizes_0001
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "prizes_0002"
down_revision: Union[str, None] = "prizes_0001"
branch_labels: Union[str, Sequence[str], None] = ("prizes",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prize_assignments",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("participation_id", sa.UUID(), nullable=False),
        sa.Column("prize_id", sa.UUID(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["participation_id"],
            ["codes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["prize_id"],
            ["prizes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        # Una participación puede ganar como máximo un premio
        sa.UniqueConstraint("participation_id", name="uq_prize_assignments_participation"),
    )
    op.create_index(
        "ix_prize_assignments_prize_id",
        "prize_assignments",
        ["prize_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_prize_assignments_prize_id", table_name="prize_assignments")
    op.drop_table("prize_assignments")
