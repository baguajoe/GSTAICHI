"""draft chapters waiting for review

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6f7a8b9c0d1'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.add_column(sa.Column('chapters_draft', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.drop_column('chapters_draft')
