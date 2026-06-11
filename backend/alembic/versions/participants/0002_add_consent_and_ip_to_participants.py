"""add consent and ip fields to participants

Revision ID: participants_0002
Revises: participants_0001
Create Date: 2026-06-11

Añade campos requeridos por RGPD y antifraude:
- consent_legal: consentimiento explícito de la base legal (obligatorio)
- consent_marketing: consentimiento marketing opcional
- ip_address: IP del participante en el momento del registro
- user_agent: agente de usuario para detección de bots
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "participants_0002"
down_revision: Union[str, None] = "participants_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "participants",
        sa.Column(
            "consent_legal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "participants",
        sa.Column(
            "consent_marketing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "participants",
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    op.add_column(
        "participants",
        sa.Column("user_agent", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("participants", "user_agent")
    op.drop_column("participants", "ip_address")
    op.drop_column("participants", "consent_marketing")
    op.drop_column("participants", "consent_legal")
