"""

Revision ID: f3e64415bb00
Revises: 33b875c6019b
Create Date: 2026-07-29 10:47:47.455298

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f3e64415bb00'
down_revision: Union[str, Sequence[str], None] = '33b875c6019b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('animaltranslations',
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('caretaker_notes', sa.String(length=255), nullable=True),
                    sa.Column('locale', sa.Enum('en', 'ru', 'uk', name='locale'), nullable=False),
                    sa.Column('parent_id', sa.UUID(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['parent_id'], ['animals.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('parent_id', 'locale', name='uq_animals_translation_locale')
                    )
    op.create_table('healthlogtranslations',
                    sa.Column('procedure_name', sa.String(length=100), nullable=False),
                    sa.Column('examination_findings', sa.String(length=255), nullable=True),
                    sa.Column('locale', sa.Enum('en', 'ru', 'uk', name='locale'), nullable=False),
                    sa.Column('parent_id', sa.UUID(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['parent_id'], ['healthlogs.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('parent_id', 'locale', name='uq_healthlogs_translation_locale')
                    )
    op.drop_constraint(op.f('animals_name_key'), 'animals', type_='unique')
    op.drop_column('animals', 'caretaker_notes')
    op.drop_column('animals', 'name')
    op.drop_column('healthlogs', 'examination_findings')
    op.drop_column('healthlogs', 'procedure_name')


def downgrade() -> None:
    op.add_column('healthlogs',
                  sa.Column('procedure_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.add_column('healthlogs',
                  sa.Column('examination_findings', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('animals', sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.add_column('animals', sa.Column('caretaker_notes', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.create_unique_constraint(op.f('animals_name_key'), 'animals', ['name'], postgresql_nulls_not_distinct=False)
    op.drop_table('healthlogtranslations')
    op.drop_table('animaltranslations')
