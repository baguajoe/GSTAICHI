"""Ask Vincent: a member's practice video on a question, and the monthly video limit

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a5
Create Date: 2026-11-08 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0d1e2f3a4b5'
down_revision = 'b9c0d1e2f3a5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('member_video_key', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('member_video_size', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('member_video_seconds', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('member_video_uploaded_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('member_video_deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_unique_constraint('uq_question_member_video_key', ['member_video_key'])
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_videos_per_month', sa.Integer(), server_default='2', nullable=False))


def downgrade():
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.drop_column('question_videos_per_month')
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_constraint('uq_question_member_video_key', type_='unique')
        batch_op.drop_column('member_video_deleted_at')
        batch_op.drop_column('member_video_uploaded_at')
        batch_op.drop_column('member_video_seconds')
        batch_op.drop_column('member_video_size')
        batch_op.drop_column('member_video_key')
