"""create codes table

Revision ID: codes_0001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "codes_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("codes",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "codes",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="unused"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_codes_code"),
    )
    # Índice primario de lookup — cada validación busca por código exacto
    op.create_index("ix_codes_code", "codes", ["code"])
    op.create_index("ix_codes_status", "codes", ["status"])


def downgrade() -> None:
    op.drop_index("ix_codes_status", table_name="codes")
    op.drop_index("ix_codes_code", table_name="codes")
    op.drop_table("codes")
