"""Create DBQueryExecuted table

Revision ID: 001
Revises:
Create Date: 2025-03-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

from ckan.model.types import make_uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dbquery_executed',
        sa.Column('id', sa.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column('query', sa.UnicodeText, nullable=False),
        sa.Column('user_id', sa.UnicodeText, nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.current_timestamp()),
    )


def downgrade():
    op.drop_table('dbquery_executed')
