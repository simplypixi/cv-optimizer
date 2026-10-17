"""Subtitle and configurable profile links.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("profiles", sa.Column("subtitle", sa.String(200), nullable=True))
    op.execute("UPDATE profiles SET subtitle = headline WHERE subtitle IS NULL AND headline IS NOT NULL")
    op.create_table("profile_links", sa.Column("id", sa.String(36), primary_key=True), sa.Column("profile_id", sa.String(36), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("label", sa.String(100), nullable=False), sa.Column("url", sa.String(1000), nullable=False), sa.Column("position", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_profile_links_profile_id", "profile_links", ["profile_id"])

def downgrade():
    op.drop_index("ix_profile_links_profile_id", "profile_links")
    op.drop_table("profile_links")
    op.drop_column("profiles", "subtitle")
