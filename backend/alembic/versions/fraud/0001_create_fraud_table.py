"""create fraud events table

Revision ID: fraud_0001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "fraud_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("fraud",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fraud_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    # Consultas de rate-limit y bloqueo filtran por IP + ventana temporal
    op.create_index("ix_fraud_events_ip_created", "fraud_events", ["ip_address", "created_at"])
    op.create_index("ix_fraud_events_event_type", "fraud_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_fraud_events_event_type", table_name="fraud_events")
    op.drop_index("ix_fraud_events_ip_created", table_name="fraud_events")
    op.drop_table("fraud_events")
