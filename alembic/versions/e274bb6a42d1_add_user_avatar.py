"""add user avatar

Revision ID: e274bb6a42d1
Revises: b7d4e2f19a03
Create Date: 2026-09-03 11:41:10.959292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e274bb6a42d1'
down_revision: Union[str, Sequence[str], None] = 'b7d4e2f19a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_key', sa.String(length=1024), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'avatar_key')