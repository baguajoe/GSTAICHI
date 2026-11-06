"""Member emails: email log, new-video announcements sent in batches, welcome timing, announce choice

Revision ID: b9c0d1e2f3a5
Revises: a8b9c0d1e2f3
Create Date: 2026-11-06 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9c0d1e2f3a5'
down_revision = 'a8b9c0d1e2f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'email_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=40), nullable=False),
        sa.Column('to_email', sa.String(length=120), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(length=300), nullable=True),
        sa.Column('status', sa.String(length=10), server_default='sending', nullable=False),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('is_test', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('dedupe_key', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['video_id'], ['video.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dedupe_key'),
    )
    with op.batch_alter_table('email_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_email_log_kind'), ['kind'], unique=False)
        batch_op.create_index(batch_op.f('ix_email_log_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_email_log_created_at'), ['created_at'], unique=False)

    op.create_table(
        'video_announcement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=10), server_default='sending', nullable=False),
        sa.Column('total', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['video.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_id'),
    )
    op.create_table(
        'announcement_recipient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=10), server_default='pending', nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['announcement_id'], ['video_announcement.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_recipient'),
    )
    op.create_index('ix_announcement_recipient_status', 'announcement_recipient', ['announcement_id', 'status'], unique=False)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('welcome_due_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('welcome_sent_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.add_column(sa.Column('announce_choice', sa.String(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.drop_column('announce_choice')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('welcome_sent_at')
        batch_op.drop_column('welcome_due_at')
    op.drop_index('ix_announcement_recipient_status', table_name='announcement_recipient')
    op.drop_table('announcement_recipient')
    op.drop_table('video_announcement')
    with op.batch_alter_table('email_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_log_created_at'))
        batch_op.drop_index(batch_op.f('ix_email_log_user_id'))
        batch_op.drop_index(batch_op.f('ix_email_log_kind'))
    op.drop_table('email_log')
