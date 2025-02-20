"""Add is_guest column to users table

Revision ID: 928a91c047fa
Revises: <REPLACE WITH ACTUAL REVISION ID>
Create Date: 2025-02-20 20:30:27.372878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '928a91c047fa'
down_revision: Union[str, None] = '<REPLACE WITH ACTUAL REVISION ID>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_guest', sa.Boolean(), nullable=True, server_default='false'))
    # Set is_guest to False for all *existing* users, if you have any.  Important!
    op.execute("UPDATE users SET is_guest = false WHERE is_guest IS NULL")
    # Now make it NOT NULL
    op.alter_column('users', 'is_guest', nullable=False)



def downgrade() -> None:
    op.drop_column('users', 'is_guest')