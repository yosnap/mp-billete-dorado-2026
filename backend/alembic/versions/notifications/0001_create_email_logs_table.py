"""create email_logs table

Revision ID: notifications_0001
Revises:
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "notifications_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("notifications",)
depends_on: Union[str, Sequence[str], None] = "participants_0001"


def upgrade() -> None:
    op.create_table(
        "email_logs",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("participant_id", sa.UUID(), nullable=False),
        # Tipo de email — uno de los 9 definidos en el dominio
        sa.Column("type", sa.String(50), nullable=False),
        # Estado del envío: pending | sent | failed
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        # Mensaje de error sin datos personales
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["participants.id"],
            name="fk_email_logs_participant",
            ondelete="CASCADE",
        ),
    )
    # Índice para consultas admin filtradas por participante
    op.create_index("ix_email_logs_participant_id", "email_logs", ["participant_id"])
    # Índice para consultas por tipo y estado (panel admin, reporting)
    op.create_index("ix_email_logs_type_status", "email_logs", ["type", "status"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_type_status", table_name="email_logs")
    op.drop_index("ix_email_logs_participant_id", table_name="email_logs")
    op.drop_table("email_logs")
