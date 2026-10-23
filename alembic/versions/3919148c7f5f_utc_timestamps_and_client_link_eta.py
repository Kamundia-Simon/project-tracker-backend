"""utc timestamps and client_link_eta

Revision ID: 3919148c7f5f
Revises: 1ea73df725b2
Create Date: 2026-10-22 14:07:24.044404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3919148c7f5f'
down_revision: Union[str, Sequence[str], None] = '1ea73df725b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Every timestamp default moves from now() — the database server's local clock,
# whatever that happens to be — to utc_timestamp(). Alembic does not diff server
# defaults unless compare_server_default is on, so this is written by hand. See
# docs/decisions/0011-time-is-stored-in-utc-and-shown-in-uk-time.md.
TIMESTAMP_COLUMNS = [
    ("users", "created_at"),
    ("project_assignments", "assigned_at"),
    ("projects", "created_at"),
    ("projects", "updated_at"),
    ("stage_transitions", "changed_at"),
    ("revisions", "requested_at"),
    ("comments", "created_at"),
    ("notifications", "created_at"),
    ("fieldwork_snapshots", "captured_at"),
    ("audit_log", "created_at"),
    ("project_markets", "created_at"),
    ("project_markets", "updated_at"),
    ("change_requests", "created_at"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('client_link_eta', sa.DateTime(), nullable=True))
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table, column,
            existing_type=sa.DateTime(),
            existing_nullable=False,
            server_default=sa.text("utc_timestamp()"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table, column,
            existing_type=sa.DateTime(),
            existing_nullable=False,
            server_default=sa.text("now()"),
        )
    op.drop_column('projects', 'client_link_eta')
