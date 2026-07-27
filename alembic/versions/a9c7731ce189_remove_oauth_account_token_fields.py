"""remove oauth_account token fields

Revision ID: a9c7731ce189
Revises: 756d89c6635f
Create Date: 2026-07-27 16:49:43.819694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c7731ce189'
down_revision: Union[str, Sequence[str], None] = '756d89c6635f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('oauthaccounts', 'access_token')
    op.drop_column('oauthaccounts', 'refresh_token')
    op.drop_column('oauthaccounts', 'expires_at')


def downgrade() -> None:
    op.add_column('oauthaccounts', sa.Column('expires_at', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('oauthaccounts', sa.Column('refresh_token', sa.VARCHAR(length=2048), autoincrement=False, nullable=True))
    op.add_column('oauthaccounts', sa.Column('access_token', sa.VARCHAR(length=2048), autoincrement=False, nullable=False))
