"""create participants table

Revision ID: participants_0001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "participants_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("participants",)
depends_on: Union[str, Sequence[str], None] = ("codes_0001", "prizes_0001")


def upgrade() -> None:
    op.create_table(
        "participants",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("code_id", sa.UUID(), nullable=False),
        sa.Column("prize_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["code_id"], ["codes.id"], name="fk_participants_code"),
        sa.ForeignKeyConstraint(["prize_id"], ["prizes.id"], name="fk_participants_prize"),
    )
    # Previene doble participación con el mismo código
    op.create_unique_constraint("uq_participants_code_id", "participants", ["code_id"])
    op.create_index("ix_participants_email", "participants", ["email"])


def downgrade() -> None:
    op.drop_index("ix_participants_email", table_name="participants")
    op.drop_constraint("uq_participants_code_id", "participants", type_="unique")
    op.drop_table("participants")
