from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class ORMOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class ExperienceIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str | None = None
    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date must not precede start date")
        return self
class ExperienceOut(ExperienceIn, ORMOut):
    id: str
class EducationIn(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
class EducationOut(EducationIn, ORMOut):
    id: str
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    url: str | None = None
class ProjectOut(ProjectIn, ORMOut):
    id: str
class ProfileIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    subtitle: str | None = Field(default=None, max_length=200)
    summary: str | None = None
class ProfilePatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    subtitle: str | None = Field(default=None, max_length=200)
    summary: str | None = None
class ProfileLinkIn(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=1000)
    position: int = Field(default=0, ge=0)
    @model_validator(mode="after")
    def check_url(self):
        from urllib.parse import urlsplit
        v = urlsplit(self.url.strip())
        if v.scheme not in ("http", "https") or not v.netloc or v.username or v.password or any(c.isspace() for c in self.url):
            raise ValueError("Link musi być prawidłowym adresem http/https")
        return self
class ProfileLinkOut(ProfileLinkIn, ORMOut):
    id: str
class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = None
    evidence_note: str | None = None
class SkillOut(ORMOut):
    id: str
    name: str
    category: str | None = None
    evidence_note: str | None = None
class ProfileOut(ProfileIn, ORMOut):
    id: str
    created_at: datetime
    experiences: list[ExperienceOut] = []
    education: list[EducationOut] = []
    projects: list[ProjectOut] = []
    skills: list[SkillOut] = []
    links: list[ProfileLinkOut] = []
