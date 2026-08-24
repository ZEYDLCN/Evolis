"""goals fields + extraction feedback

Revision ID: 9f1b2c7e5a3d
Revises: 24cacfbe00c0
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f1b2c7e5a3d'
down_revision: Union[str, Sequence[str], None] = '24cacfbe00c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('goals') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('metric_key', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('target_value', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('target_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))

    op.create_table(
        'extraction_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entry_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('original_extraction', sa.JSON(), nullable=False),
        sa.Column('corrected_extraction', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['entry_id'], ['entries.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_extraction_feedback_entry_id'), 'extraction_feedback', ['entry_id'], unique=False)
    op.create_index(op.f('ix_extraction_feedback_user_id'), 'extraction_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_extraction_feedback_user_id'), table_name='extraction_feedback')
    op.drop_index(op.f('ix_extraction_feedback_entry_id'), table_name='extraction_feedback')
    op.drop_table('extraction_feedback')

    with op.batch_alter_table('goals') as batch_op:
        batch_op.drop_column('completed_at')
        batch_op.drop_column('source')
        batch_op.drop_column('target_date')
        batch_op.drop_column('target_value')
        batch_op.drop_column('metric_key')
        batch_op.drop_column('description')
