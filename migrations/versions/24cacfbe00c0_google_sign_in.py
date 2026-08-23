"""google sign-in

Revision ID: 24cacfbe00c0
Revises: a584a8c43db3
Create Date: 2026-08-23 22:34:36.882070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24cacfbe00c0'
down_revision: Union[str, Sequence[str], None] = 'a584a8c43db3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # batch_alter_table (not plain op.alter_column/add_column) so this also
    # runs on SQLite, which has no ALTER COLUMN and needs Alembic to
    # recreate the table under the hood.
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('google_sub', sa.String(length=255), nullable=True))
        batch_op.alter_column('hashed_password',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
        batch_op.create_index(batch_op.f('ix_users_google_sub'), ['google_sub'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_google_sub'))
        batch_op.alter_column('hashed_password',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
        batch_op.drop_column('google_sub')
