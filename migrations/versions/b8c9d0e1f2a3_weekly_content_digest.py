"""weekly "New this week" digest email (replaces the per-video emails)

Adds digest_sent_at to articles and videos, and the content_digest / digest_recipient tables.
So the first digest does not list the whole library, everything that members could already see more than
7 days ago, and every video that already had its own email, counts as sent. Newer things (such as Vincent's
10 articles from November 2026) go into the next digest.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-11-18 16:00:00.000000

"""
from datetime import datetime, timedelta

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.add_column(sa.Column('digest_sent_at', sa.DateTime(), nullable=True))
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.add_column(sa.Column('digest_sent_at', sa.DateTime(), nullable=True))

    op.create_table(
        'content_digest',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=10), server_default='weekly', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('article_ids', sa.JSON(), nullable=False),
        sa.Column('video_ids', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=10), server_default='sending', nullable=False),
        sa.Column('total', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'digest_recipient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('digest_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=10), server_default='pending', nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['digest_id'], ['content_digest.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('digest_id', 'user_id', name='uq_digest_recipient'),
    )
    op.create_index('ix_digest_recipient_status', 'digest_recipient', ['digest_id', 'status'], unique=False)

    now = datetime.utcnow()
    cutoff = now - timedelta(days=7)
    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE article SET digest_sent_at = :now "
        "WHERE COALESCE(publish_at, created_at) < :cutoff"), {"now": now, "cutoff": cutoff})
    bind.execute(sa.text(
        "UPDATE video SET digest_sent_at = :now "
        "WHERE announce_choice IS NOT NULL "  # already had its own email (or the teacher chose No)
        "OR (is_published AND status = 'ready' AND hls_master_path IS NOT NULL "
        "    AND COALESCE(publish_at, created_at) < :cutoff)"), {"now": now, "cutoff": cutoff})


def downgrade():
    op.drop_index('ix_digest_recipient_status', table_name='digest_recipient')
    op.drop_table('digest_recipient')
    op.drop_table('content_digest')
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.drop_column('digest_sent_at')
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_column('digest_sent_at')
