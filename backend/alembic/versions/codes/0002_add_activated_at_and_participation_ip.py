"""add activated_at and participation_ip to codes

Revision ID: codes_0002
Revises: codes_0001
Create Date: 2026-06-11

La migración 0001 creó la tabla con los campos mínimos.
Esta añade los campos requeridos para el flujo de validación de la fase-02:
- activated_at: momento en que el código entra en vigor para la campaña
- participation_ip: IP del participante (base legal RGPD — registrada en validación)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "codes_0002"
down_revision: Union[str, None] = "codes_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "codes",
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "codes",
        sa.Column("participation_ip", sa.String(45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("codes", "participation_ip")
    op.drop_column("codes", "activated_at")
