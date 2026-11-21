"""Initial schema

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forget_processes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("key", sa.String(512), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forget_processes_tenant_id", "forget_processes", ["tenant_id"])
    op.create_index("ix_forget_processes_requested_at", "forget_processes", ["requested_at"])

    op.create_table(
        "process_subscribers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "process_id",
            sa.Uuid(),
            sa.ForeignKey("forget_processes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("process_id", "name"),
    )

    op.create_table(
        "subscriber_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "process_subscriber_id",
            sa.Integer(),
            sa.ForeignKey("process_subscribers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event", sa.String(16), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_subscriber_results_process_subscriber_id",
        "subscriber_results",
        ["process_subscriber_id"],
    )

    op.create_table(
        "subscribers",
        sa.Column("name", sa.String(128), primary_key=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("subscribers")
    op.drop_table("subscriber_results")
    op.drop_table("process_subscribers")
    op.drop_table("forget_processes")
