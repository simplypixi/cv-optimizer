"""Initial profile data structures.
Revision ID: 0001_initial
Revises:
"""
from alembic import op
from app.database import Base
from app import models  # noqa: F401
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=[Base.metadata.tables[x] for x in ("profiles", "experiences", "education", "projects", "skills", "profile_skills")])
    # Historical 0001 schema did not contain subtitle; keep fresh installations compatible with 0003.
    from sqlalchemy import inspect
    if "subtitle" in {c["name"] for c in inspect(bind).get_columns("profiles")}:
        op.drop_column("profiles", "subtitle")

def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=[Base.metadata.tables[x] for x in ("profile_skills", "projects", "education", "experiences", "skills", "profiles")])
