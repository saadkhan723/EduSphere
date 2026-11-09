
"""Add Google Drive fields to study materials

Revision ID: 23fc6073cd0f
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = '23fc6073cd0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('study_materials') as batch_op:
        batch_op.add_column(
            sa.Column('drive_file_id', sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column('drive_folder_id', sa.String(length=255), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('study_materials') as batch_op:
        batch_op.drop_column('drive_folder_id')
        batch_op.drop_column('drive_file_id')
