"""Add student table

Revision ID: 91b1f470a94f
Revises: bfff16692b4a
Create Date: 2024-03-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91b1f470a94f'
down_revision = 'bfff16692b4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'student',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('class_name', sa.String(255), nullable=False),
        sa.Column('number', sa.String(50), nullable=True),
        sa.Column('parent_name', sa.String(255), nullable=True),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['school.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_name'), 'student', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_student_name'), table_name='student')
    op.drop_table('student')
