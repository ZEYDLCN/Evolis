"""evolution events (turning points / decisions)

Revision ID: 3e7a1c9b2f4d
Revises: 9f1b2c7e5a3d
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e7a1c9b2f4d'
down_revision: Union[str, Sequence[str], None] = '9f1b2c7e5a3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'evolution_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('entry_id', sa.String(length=36), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['entry_id'], ['entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evolution_events_user_id'), 'evolution_events', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_evolution_events_user_id'), table_name='evolution_events')
    op.drop_table('evolution_events')
