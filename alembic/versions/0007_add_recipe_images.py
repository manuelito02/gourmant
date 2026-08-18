"""add recipe images

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-02
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("image_filename", sa.String(255), nullable=True))

    op.create_table(
        "step_images",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "step_id",
            sa.Integer,
            sa.ForeignKey("steps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("step_id", "position", name="uq_step_image_position"),
    )
    op.create_index("ix_step_images_step_id", "step_images", ["step_id"])


def downgrade() -> None:
    op.drop_index("ix_step_images_step_id", table_name="step_images")
    op.drop_table("step_images")
    op.drop_column("recipes", "image_filename")
