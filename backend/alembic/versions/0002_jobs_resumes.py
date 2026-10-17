"""jobs and resume versions

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('job_postings', sa.Column('id',sa.String(36),primary_key=True),sa.Column('profile_id',sa.String(36),sa.ForeignKey('profiles.id',ondelete='CASCADE'),nullable=False),sa.Column('title',sa.String(200),nullable=False),sa.Column('company',sa.String(200)),sa.Column('description',sa.Text(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True)))
    op.create_index('ix_job_postings_profile_id','job_postings',['profile_id'])
    op.create_table('resume_versions', sa.Column('id',sa.String(36),primary_key=True),sa.Column('profile_id',sa.String(36),sa.ForeignKey('profiles.id',ondelete='CASCADE'),nullable=False),sa.Column('job_id',sa.String(36),sa.ForeignKey('job_postings.id',ondelete='SET NULL')),sa.Column('content_json',sa.Text(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True)))
    op.create_index('ix_resume_versions_profile_id','resume_versions',['profile_id'])

def downgrade():
    op.drop_index('ix_resume_versions_profile_id','resume_versions')
    op.drop_table('resume_versions')
    op.drop_index('ix_job_postings_profile_id','job_postings')
    op.drop_table('job_postings')
