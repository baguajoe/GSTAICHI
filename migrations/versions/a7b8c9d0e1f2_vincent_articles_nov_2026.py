"""Vincent Chu's articles (November 2026): 10 new members-only articles, a "Training" article category, and
"Three Levels of Tai Chi Chuan Practice" and "Cultivation and Training in Chinese Martial Art" moved into it.

The articles were converted from Word by scripts/convert_vincent_articles.py into
src/api/seed_data/vincent_chu_articles_2026_11.json. An article whose title already exists is not added again.

Revision ID: a7b8c9d0e1f2
Revises: d1e2f3a4b5c6
Create Date: 2026-11-18 14:00:00.000000

"""
from alembic import op

from api.article_batches import load_batch, apply_batch


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    result = apply_batch(op.get_bind(), load_batch("vincent_chu_articles_2026_11.json"))
    print(f"Vincent's articles: {len(result['added'])} added, {len(result['skipped'])} already there, "
          f"{len(result['moved'])} moved to Training.")


def downgrade():
    # Articles may have been read, edited or linked to since: they are not deleted automatically.
    pass
