"""

Revision ID: ccd2f695bfe7
Revises: 37c7a62f623f
Create Date: 2026-07-24 13:29:35.533262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccd2f695bfe7'
down_revision: Union[str, Sequence[str], None] = '37c7a62f623f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('permissions_resource_id_fkey'), 'permissions', type_='foreignkey')
    op.create_foreign_key(None, 'permissions', 'resources', ['resource_id'], ['id'], ondelete='RESTRICT')
    op.drop_column('refreshtokens', 'user_agent')


def downgrade() -> None:
    op.add_column('refreshtokens', sa.Column('user_agent', sa.VARCHAR(length=400), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'permissions', type_='foreignkey')
    op.create_foreign_key(op.f('permissions_resource_id_fkey'), 'permissions', 'resources', ['resource_id'], ['id'], ondelete='CASCADE')
