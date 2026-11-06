"""Ask Vincent details (subject, lesson, time, idea flag) and the member's private profile

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subject', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('lesson_video_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('video_time', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('member_plan', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('is_corner_idea', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.create_foreign_key('fk_question_lesson_video', 'video', ['lesson_video_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo_path', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('email_new_videos', sa.Boolean(), server_default=sa.true(), nullable=False))
        batch_op.add_column(sa.Column('email_answers', sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('email_answers')
        batch_op.drop_column('email_new_videos')
        batch_op.drop_column('photo_path')

    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_constraint('fk_question_lesson_video', type_='foreignkey')
        batch_op.drop_column('is_corner_idea')
        batch_op.drop_column('member_plan')
        batch_op.drop_column('video_time')
        batch_op.drop_column('lesson_video_id')
        batch_op.drop_column('subject')
