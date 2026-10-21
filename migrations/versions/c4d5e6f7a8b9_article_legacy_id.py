"""article legacy id

Revision ID: c4d5e6f7a8b9
Revises: b3c1d2e4f5a6
Create Date: 2026-10-21 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = 'b3c1d2e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.add_column(sa.Column('legacy_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_article_legacy_id', ['legacy_id'])


def downgrade():
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_constraint('uq_article_legacy_id', type_='unique')
        batch_op.drop_column('legacy_id')
