"""plan sandbox paypal id

Revision ID: b3c1d2e4f5a6
Revises: fca09183db2a
Create Date: 2026-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c1d2e4f5a6'
down_revision = 'fca09183db2a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paypal_sandbox_plan_id', sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint('uq_plan_paypal_sandbox_plan_id', ['paypal_sandbox_plan_id'])


def downgrade():
    with op.batch_alter_table('plan', schema=None) as batch_op:
        batch_op.drop_constraint('uq_plan_paypal_sandbox_plan_id', type_='unique')
        batch_op.drop_column('paypal_sandbox_plan_id')
