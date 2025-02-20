"""Add cascade delete to room_participants

Revision ID: <REPLACE WITH ACTUAL REVISION ID>
Revises: 0001_manual
Create Date: 2025-02-19 ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '<REPLACE WITH ACTUAL REVISION ID>'  # e.g., 'abcdef123456' - Use the actual ID from the filename
down_revision: Union[str, None] = '0001_manual'  # This is correct, points to the *previous* migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraints (without cascade)
    op.drop_constraint('room_participants_room_id_fkey', 'room_participants', type_='foreignkey')
    op.drop_constraint('room_participants_user_id_fkey', 'room_participants', type_='foreignkey')

    # Recreate the foreign key constraints *with* ON DELETE CASCADE
    op.create_foreign_key(
        'room_participants_room_id_fkey',  # Constraint name
        'room_participants',  # Source table
        'rooms',  # Target table
        ['room_id'],  # Source column(s)
        ['id'],  # Target column(s)
        ondelete='CASCADE'  # Add ON DELETE CASCADE
    )
    op.create_foreign_key(
        'room_participants_user_id_fkey',
        'room_participants',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop the constraints with cascade
    op.drop_constraint('room_participants_room_id_fkey', 'room_participants', type_='foreignkey')
    op.drop_constraint('room_participants_user_id_fkey', 'room_participants', type_='foreignkey')

    # Recreate the constraints *without* cascade (original state)
    op.create_foreign_key(
        'room_participants_room_id_fkey',
        'room_participants',
        'rooms',
        ['room_id'],
        ['id']
    )
    op.create_foreign_key(
        'room_participants_user_id_fkey',
        'room_participants',
        'users',
        ['user_id'],
        ['id']
    )