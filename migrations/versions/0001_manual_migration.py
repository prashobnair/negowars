"""initial manual migration

Revision ID: 0001_manual
Revises: 
Create Date: 2024-02-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0001_manual'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'))
    )
    
    # Create rooms table
    op.create_table('rooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('status', sa.String(20), 
                 server_default='waiting'),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()')),
        sa.Column('game_state', postgresql.JSONB())
    )
    
    # Create room_participants association table
    op.create_table('room_participants',
        sa.Column('user_id', sa.Integer(), 
                 sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('room_id', sa.Integer(), 
                 sa.ForeignKey('rooms.id'), primary_key=True),
        sa.Column('role', sa.String())
    )
    
    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), 
                 sa.ForeignKey('users.id'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False)
    )
    
    # Create indexes
    op.create_index('idx_rooms_status', 'rooms', ['status'])
    op.create_index('idx_sessions_user', 'sessions', ['user_id'])

def downgrade():
    op.drop_table('sessions')
    op.drop_table('room_participants')
    op.drop_table('rooms')
    op.drop_table('users')