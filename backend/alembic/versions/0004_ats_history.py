"""Persistent diagnostics and safe restoration.
Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('resume_versions',sa.Column('restored_from_id',sa.String(36),nullable=True))
    op.create_table('ats_reports',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('resume_id',sa.String(36),sa.ForeignKey('resume_versions.id',ondelete='CASCADE'),nullable=False),
        sa.Column('format',sa.String(8),nullable=False),
        sa.Column('result_json',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_ats_reports_resume_id','ats_reports',['resume_id'])

def downgrade():
    op.drop_index('ix_ats_reports_resume_id','ats_reports')
    op.drop_table('ats_reports')
    op.drop_column('resume_versions','restored_from_id')
