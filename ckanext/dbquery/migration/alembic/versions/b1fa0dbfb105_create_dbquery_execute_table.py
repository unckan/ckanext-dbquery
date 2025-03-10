""" create dbquery execute table

Revision ID: b1fa0dbfb105
Revises: 
Create Date: 2025-03-10 18:11:50.536615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1fa0dbfb105'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dbquery_executed',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('dbquery_executed')
