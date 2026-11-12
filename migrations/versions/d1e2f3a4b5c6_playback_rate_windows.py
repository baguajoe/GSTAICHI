"""playback rate windows: sustained-speed and full-fetch tracking per playback session

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-11-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c0d1e2f3a4b5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('playback_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('window_started_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('window_pieces', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('window_seeks', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('fast_windows', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('fetched_all_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('playback_session', schema=None) as batch_op:
        batch_op.drop_column('fetched_all_at')
        batch_op.drop_column('fast_windows')
        batch_op.drop_column('window_seeks')
        batch_op.drop_column('window_pieces')
        batch_op.drop_column('window_started_at')
