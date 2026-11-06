"""When members agreed to the health disclaimer and Terms of Use; refund window setting

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-11-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8b9c0d1e2f3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agreed_terms_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('refund_days', sa.Integer(), server_default='7', nullable=False))


def downgrade():
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.drop_column('refund_days')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('agreed_terms_at')
