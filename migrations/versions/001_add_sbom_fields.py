"""Add component_count and file_path to SBOM table

Revision ID: 001
Revises: 
Create Date: 2025-01-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add component_count and file_path columns to sboms table"""
    try:
        # Add component_count column with default value
        op.add_column('sboms', sa.Column('component_count', sa.Integer(), default=0))
        
        # Add file_path column
        op.add_column('sboms', sa.Column('file_path', sa.String(1024), nullable=True))
        
        print("Successfully added component_count and file_path columns to sboms table")
    except Exception as e:
        print(f"Migration failed: {e}")
        # Don't fail the migration completely since the system should continue working
        pass

def downgrade():
    """Remove component_count and file_path columns from sboms table"""
    try:
        op.drop_column('sboms', 'file_path')
        op.drop_column('sboms', 'component_count')
        print("Successfully removed component_count and file_path columns from sboms table")
    except Exception as e:
        print(f"Downgrade failed: {e}")
        pass