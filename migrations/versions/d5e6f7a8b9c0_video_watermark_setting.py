"""video watermark setting (off by default)

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('video_watermark', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade():
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.drop_column('video_watermark')
