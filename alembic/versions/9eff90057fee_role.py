"""

Revision ID: 9eff90057fee_permissions
Revises: dcc41b323671_change_user_model
Create Date: 2026-07-23 11:08:52.850047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eff90057fee_permissions'
down_revision: Union[str, Sequence[str], None] = 'dcc41b323671_change_user_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('permissions',
    sa.Column('role', sa.Enum('user', 'admin', 'staff', name='role'), nullable=False),
    sa.Column('resource', sa.String(length=100), nullable=False),
    sa.Column('action', sa.Enum('read', 'create', 'update', 'delete', name='policy'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('permissions')
