from datetime import date
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .database import get_db
from .models import Profile, Experience, Education, Project, Skill, ProfileSkill, ProfileLink
from .schemas import (ProfileIn, ProfilePatch, ProfileOut, ExperienceIn, ExperienceOut,
                      EducationIn, EducationOut, ProjectIn, ProjectOut, SkillIn, SkillOut, ProfileLinkIn, ProfileLinkOut)

app = FastAPI(title="CV Optimizer API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])

def get_profile(db: Session, profile_id: str):
    profile = db.scalar(select(Profile).where(Profile.id == profile_id).options(
        selectinload(Profile.experiences), selectinload(Profile.education),
        selectinload(Profile.projects), selectinload(Profile.links), selectinload(Profile.skills).selectinload(ProfileSkill.skill)))
    if profile is None: raise HTTPException(404, "Profile not found")
    return profile

def serialize(profile):
    result = ProfileOut.model_validate({"id":profile.id,"full_name":profile.full_name,"email":profile.email,"phone":profile.phone,"location":profile.location,"headline":profile.headline,"subtitle":profile.subtitle,"summary":profile.summary,"created_at":profile.created_at,"experiences":profile.experiences,"education":profile.education,"projects":profile.projects,"links":profile.links,"skills":[]}).model_dump(mode="json")
    result["skills"] = [SkillOut(id=s.id, name=s.skill.name, category=s.skill.category,
                                  evidence_note=s.evidence_note).model_dump() for s in profile.skills]
    return result

@app.get("/api/v1/health")
def health(): return {"status": "ok"}

@app.post("/api/v1/profiles", status_code=201)
def create_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    profile = Profile(**payload.model_dump())
    db.add(profile); db.commit()
    return serialize(get_profile(db, profile.id))

@app.get("/api/v1/profiles")
def list_profiles(db: Session = Depends(get_db)):
    ids = db.scalars(select(Profile.id).order_by(Profile.created_at.desc())).all()
    return [serialize(get_profile(db, pid)) for pid in ids]

@app.get("/api/v1/profiles/{profile_id}")
def read_profile(profile_id: str, db: Session = Depends(get_db)):
    return serialize(get_profile(db, profile_id))

@app.patch("/api/v1/profiles/{profile_id}")
def update_profile(profile_id: str, payload: ProfilePatch, db: Session = Depends(get_db)):
    profile = get_profile(db, profile_id)
    for name, value in payload.model_dump(exclude_unset=True).items():
        if name == "full_name" and value is None: raise HTTPException(422, "full_name cannot be null")
        setattr(profile, name, value)
    db.commit()
    return serialize(get_profile(db, profile_id))

@app.delete("/api/v1/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = get_profile(db, profile_id)
    db.delete(profile); db.commit()

@app.post("/api/v1/profiles/{profile_id}/experiences", status_code=201, response_model=ExperienceOut)
def add_experience(profile_id: str, payload: ExperienceIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    row = Experience(profile_id=profile_id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.post("/api/v1/profiles/{profile_id}/education", status_code=201, response_model=EducationOut)
def add_education(profile_id: str, payload: EducationIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    row = Education(profile_id=profile_id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.post("/api/v1/profiles/{profile_id}/projects", status_code=201, response_model=ProjectOut)
def add_project(profile_id: str, payload: ProjectIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    row = Project(profile_id=profile_id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.post("/api/v1/profiles/{profile_id}/skills", status_code=201, response_model=SkillOut)
def add_skill(profile_id: str, payload: SkillIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    name = payload.name.strip()
    skill = db.scalar(select(Skill).where(Skill.name == name))
    if skill is None:
        skill = Skill(name=name, category=payload.category)
        db.add(skill); db.flush()
    existing = db.scalar(select(ProfileSkill).where(ProfileSkill.profile_id == profile_id, ProfileSkill.skill_id == skill.id))
    if existing: raise HTTPException(409, "Skill already assigned")
    assignment = ProfileSkill(profile_id=profile_id, skill_id=skill.id, evidence_note=payload.evidence_note)
    db.add(assignment); db.commit(); db.refresh(assignment)
    return SkillOut(id=assignment.id, name=skill.name, category=skill.category, evidence_note=assignment.evidence_note)

@app.post("/api/v1/profiles/{profile_id}/links", status_code=201, response_model=ProfileLinkOut)
def add_link(profile_id: str, payload: ProfileLinkIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    row = ProfileLink(profile_id=profile_id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.patch("/api/v1/profiles/{profile_id}/links/{link_id}", response_model=ProfileLinkOut)
def update_link(profile_id: str, link_id: str, payload: ProfileLinkIn, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    row = db.scalar(select(ProfileLink).where(ProfileLink.id == link_id, ProfileLink.profile_id == profile_id))
    if row is None: raise HTTPException(404, "Link not found")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    db.commit(); db.refresh(row)
    return row

CHILD_TYPES = {"experiences": Experience, "education": Education, "projects": Project, "skills": ProfileSkill, "links": ProfileLink}
@app.delete("/api/v1/profiles/{profile_id}/{kind}/{item_id}", status_code=204)
def remove_child(profile_id: str, kind: str, item_id: str, db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    model = CHILD_TYPES.get(kind)
    if model is None: raise HTTPException(404, "Unknown section")
    item = db.scalar(select(model).where(model.id == item_id, model.profile_id == profile_id))
    if item is None: raise HTTPException(404, "Item not found")
    db.delete(item); db.commit()


# Local-only extended workflow
import json
from io import BytesIO
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from .models import JobPosting, ResumeVersion, ATSReport
from .optimizer import analyze
from .documents import read_document, render_resume, lint

class JobIn(BaseModel):
    profile_id: str
    title: str = Field(min_length=1,max_length=200)
    company: str | None = None
    description: str = Field(min_length=1,max_length=60000)

class ResumeIn(BaseModel):
    profile_id: str
    job_id: str | None = None
    content: dict

@app.post('/api/v1/documents/import')
async def import_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(('.pdf','.docx')):raise HTTPException(422,'Obsługiwane formaty: PDF i DOCX')
    contents=await file.read(5_000_001)
    if len(contents)>5_000_000:raise HTTPException(413,'Limit pliku 5 MB')
    try:text=read_document(contents,file.filename)
    except Exception as exc:raise HTTPException(422,str(exc)) from exc
    return {'filename':file.filename,'text':text,'lint':lint(text)}

@app.post('/api/v1/jobs',status_code=201)
def create_job(payload:JobIn,db:Session=Depends(get_db)):
    get_profile(db,payload.profile_id)
    j=JobPosting(**payload.model_dump());db.add(j);db.commit();db.refresh(j)
    return {'id':j.id,**payload.model_dump()}

@app.get('/api/v1/profiles/{profile_id}/jobs')
def list_jobs(profile_id:str,db:Session=Depends(get_db)):
    get_profile(db,profile_id)
    return [{'id':j.id,'title':j.title,'company':j.company,'description':j.description} for j in db.scalars(select(JobPosting).where(JobPosting.profile_id==profile_id)).all()]

@app.delete('/api/v1/jobs/{job_id}',status_code=204)
def delete_job(job_id:str,db:Session=Depends(get_db)):
    j=db.get(JobPosting,job_id)
    if not j:raise HTTPException(404,'Oferta nie istnieje')
    db.delete(j);db.commit()

@app.get('/api/v1/jobs/{job_id}/analysis')
def analyze_job(job_id:str,db:Session=Depends(get_db)):
    job=db.get(JobPosting,job_id)
    if not job:raise HTTPException(404,'Oferta nie istnieje')
    p=serialize(get_profile(db,job.profile_id))
    return analyze(p,{'description':job.description})

@app.post('/api/v1/resumes',status_code=201)
def create_resume(payload:ResumeIn,db:Session=Depends(get_db)):
    get_profile(db,payload.profile_id)
    if payload.job_id:
        job=db.get(JobPosting,payload.job_id)
        if not job or job.profile_id!=payload.profile_id:raise HTTPException(422,'Oferta nie należy do profilu')
    if not payload.content.get('full_name'):raise HTTPException(422,'Brakuje imienia i nazwiska')
    if payload.content.get('template','classic') not in ('classic','editorial','modern','compact'):raise HTTPException(422,'Nieznany szablon CV')
    if not isinstance(payload.content.get('career_path',False),bool):raise HTTPException(422,'career_path musi być typu boolean')
    if len(json.dumps(payload.content,ensure_ascii=False))>200000:raise HTTPException(413,'Zbyt duży dokument')
    row=ResumeVersion(profile_id=payload.profile_id,job_id=payload.job_id,content_json=json.dumps(payload.content,ensure_ascii=False))
    db.add(row);db.commit();db.refresh(row)
    return {'id':row.id,'created_at':row.created_at.isoformat()}

@app.get('/api/v1/profiles/{profile_id}/resumes')
def list_resumes(profile_id:str,db:Session=Depends(get_db)):
    get_profile(db,profile_id)
    return [{'id':r.id,'job_id':r.job_id,'created_at':r.created_at.isoformat(),'restored_from_id':r.restored_from_id,'content':json.loads(r.content_json)} for r in db.scalars(select(ResumeVersion).where(ResumeVersion.profile_id==profile_id).order_by(ResumeVersion.created_at.desc())).all()]

@app.get('/api/v1/resumes/{resume_id}/export')
def export_resume(resume_id:str,format:str='docx',db:Session=Depends(get_db)):
    row=db.get(ResumeVersion,resume_id)
    if not row:raise HTTPException(404,'Wersja nie istnieje')
    if format not in ('docx','pdf'):raise HTTPException(422,'Wybierz PDF lub DOCX')
    raw=render_resume(json.loads(row.content_json))
    if format=='pdf':
        import subprocess,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'cv.docx';source.write_bytes(raw)
            try:
                run=subprocess.run(['libreoffice','-env:UserInstallation=file://'+t+'/lo','--headless','--convert-to','pdf','--outdir',t,str(source)],capture_output=True,timeout=45)
                if run.returncode!=0 or not (Path(t)/'cv.pdf').exists():raise RuntimeError('LibreOffice nie wygenerował PDF')
                raw=(Path(t)/'cv.pdf').read_bytes()
            except (OSError,subprocess.TimeoutExpired,RuntimeError) as exc:raise HTTPException(503,'PDF wymaga zainstalowanego LibreOffice: '+str(exc)) from exc
    mimetype='application/pdf' if format=='pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return StreamingResponse(BytesIO(raw),media_type=mimetype,headers={'Content-Disposition':f'attachment; filename="cv-{resume_id[:8]}.{format}"'})

@app.get('/api/v1/resumes/{resume_id}/lint')
def lint_resume(resume_id:str,db:Session=Depends(get_db)):
    row=db.get(ResumeVersion,resume_id)
    if not row:raise HTTPException(404,'Wersja nie istnieje')
    raw=render_resume(json.loads(row.content_json))
    return lint(read_document(raw,'cv.docx'))

# Import of user-requested LinkedIn data archive; preview before explicit confirmation.
from .linkedin_import import read_archive, fingerprint, MAX_ARCHIVE
from pydantic import ValidationError

class LinkedInCommit(BaseModel):
    sections: dict[str, list[dict]]

@app.post('/api/v1/profiles/{profile_id}/linkedin/preview')
async def linkedin_preview(profile_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    get_profile(db, profile_id)
    if not (file.filename or '').lower().endswith('.zip'):
        raise HTTPException(422, 'Wybierz archiwum ZIP pobrane z LinkedIn')
    data = await file.read(MAX_ARCHIVE + 1)
    try: return read_archive(data)
    except (ValueError, __import__('zipfile').BadZipFile) as exc: raise HTTPException(422, str(exc)) from exc

@app.post('/api/v1/profiles/{profile_id}/linkedin/commit')
def linkedin_commit(profile_id: str, payload: LinkedInCommit, db: Session = Depends(get_db)):
    profile = get_profile(db, profile_id)
    allowed = {'experiences': (Experience, ExperienceIn), 'education': (Education, EducationIn),
               'projects': (Project, ProjectIn), 'skills': (Skill, SkillIn)}
    if set(payload.sections) - set(allowed): raise HTTPException(422, 'Nieznany rodzaj wpisów')
    if sum(len(v) for v in payload.sections.values()) > 700: raise HTTPException(413, 'Zbyt wiele wpisów')
    added = {k: 0 for k in allowed}
    skipped = {k: 0 for k in allowed}
    try:
        for kind, rows in payload.sections.items():
            model, schema = allowed[kind]
            if kind == 'skills':
                existing = {fingerprint('skills', {'name': ps.skill.name}) for ps in profile.skills}
            else:
                existing = {fingerprint(kind, {c.name: getattr(v,c.name).isoformat() if isinstance(getattr(v,c.name),date) else getattr(v,c.name) for c in model.__table__.columns if c.name not in ('id','profile_id')}) for v in getattr(profile,kind)}
            for raw in rows:
                entry = schema.model_validate(raw).model_dump()
                key = fingerprint(kind, {k:(v.isoformat() if isinstance(v,date) else v) for k,v in entry.items()})
                if key in existing:
                    skipped[kind]+=1
                    continue
                existing.add(key)
                if kind == 'skills':
                    skill = db.scalar(select(Skill).where(Skill.name == entry['name']))
                    if skill is None:
                        skill = Skill(name=entry['name'], category=entry.get('category'))
                        db.add(skill); db.flush()
                    db.add(ProfileSkill(profile_id=profile_id,skill_id=skill.id,evidence_note=entry.get('evidence_note')))
                else:
                    db.add(model(profile_id=profile_id,**entry))
                added[kind]+=1
        db.commit()
    except (ValidationError, ValueError) as exc:
        db.rollback(); raise HTTPException(422,str(exc)) from exc
    return {'added':added,'duplicates_skipped':skipped}

# Manual, on-demand diagnostic: never triggered by profile/editor changes.
from .ats_diagnostics import diagnose

@app.post('/api/v1/resumes/{resume_id}/ats-check')
def ats_check(resume_id: str, format: str = 'docx', db: Session = Depends(get_db)):
    """Check real generated DOCX, optionally real PDF. Caller must explicitly invoke."""
    row = db.get(ResumeVersion, resume_id)
    if row is None:
        raise HTTPException(404, 'Wersja CV nie istnieje')
    if format not in ('docx','pdf'):
        raise HTTPException(422, 'Wybierz docx lub pdf')
    raw = render_resume(json.loads(row.content_json))
    pdf = None
    if format == 'pdf':
        import subprocess, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as t:
            source = Path(t)/'cv.docx'
            source.write_bytes(raw)
            try:
                run = subprocess.run(['libreoffice', '-env:UserInstallation=file://'+t+'/lo', '--headless', '--convert-to', 'pdf', '--outdir', t, str(source)], capture_output=True, timeout=45)
                if run.returncode != 0 or not (Path(t)/'cv.pdf').exists():
                    raise RuntimeError('Konwersja PDF nie powiodła się')
                pdf = (Path(t)/'cv.pdf').read_bytes()
            except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
                raise HTTPException(503, 'Kontrola PDF wymaga LibreOffice: '+str(exc)) from exc
    result={'resume_id':resume_id,'format':format,**diagnose(raw,pdf)}
    db.add(ATSReport(resume_id=resume_id,format=format,result_json=json.dumps(result,ensure_ascii=False)))
    db.commit()
    return result

# Saved reports are immutable snapshots. Restoring creates another version, not an overwrite.
def report_payload(report: ATSReport):
    return {'id':report.id,'resume_id':report.resume_id,'format':report.format,
            'created_at':report.created_at.isoformat(),'result':json.loads(report.result_json)}

@app.get('/api/v1/resumes/{resume_id}/ats-history')
def ats_history(resume_id: str, db: Session = Depends(get_db)):
    if db.get(ResumeVersion,resume_id) is None: raise HTTPException(404,'Wersja CV nie istnieje')
    rows=db.scalars(select(ATSReport).where(ATSReport.resume_id==resume_id).order_by(ATSReport.created_at.desc(), ATSReport.id.desc())).all()
    return [report_payload(r) for r in rows]

@app.get('/api/v1/profiles/{profile_id}/ats-history')
def profile_ats_history(profile_id: str, db: Session = Depends(get_db)):
    get_profile(db,profile_id)
    rows=db.scalars(select(ATSReport).join(ResumeVersion, ATSReport.resume_id==ResumeVersion.id)
                    .where(ResumeVersion.profile_id==profile_id)
                    .order_by(ATSReport.created_at.desc(),ATSReport.id.desc())).all()
    return [report_payload(r) for r in rows]

@app.get('/api/v1/ats-reports/compare')
def compare_reports(before_id: str, after_id: str, db: Session = Depends(get_db)):
    before=db.get(ATSReport,before_id); after=db.get(ATSReport,after_id)
    if not before or not after: raise HTTPException(404,'Raport nie istnieje')
    old_resume=db.get(ResumeVersion,before.resume_id); new_resume=db.get(ResumeVersion,after.resume_id)
    if old_resume.profile_id!=new_resume.profile_id: raise HTTPException(422,'Raporty muszą należeć do jednego profilu')
    if before.format!=after.format: raise HTTPException(422,'Porównuj raporty tego samego formatu')
    b=json.loads(before.result_json); a=json.loads(after.result_json)
    diffs={}
    for name in ('greenhouse','workday','lever'):
        v1=b['profiles'][name]['score']; v2=a['profiles'][name]['score']
        first={x['id']:x for x in b['profiles'][name]['rules']}
        second={x['id']:x for x in a['profiles'][name]['rules']}
        changes=[{'rule_id':key,'title':second[key]['title'],'before':first[key]['status'],
                  'after':second[key]['status'],'detail':second[key]['detail']}
                 for key in first.keys() & second.keys() if first[key]['status']!=second[key]['status']]
        diffs[name]={'before':v1,'after':v2,'delta':None if v1 is None or v2 is None else v2-v1,
                     'coverage_before':b['profiles'][name]['coverage'],'coverage_after':a['profiles'][name]['coverage'],
                     'changed_rules':changes}
    return {'before_id':before_id,'after_id':after_id,'format':before.format,'profiles':diffs,
            'note':'Autorskie wskaźniki techniczne, nie wyniki systemów ATS. Różnice mogą wynikać również ze zmian wag lub reguł.'}

@app.get('/api/v1/resumes/compare-content')
def compare_resume_content(before_id: str, after_id: str, db: Session = Depends(get_db)):
    from .resume_diff import compare_content
    old=db.get(ResumeVersion,before_id)
    new=db.get(ResumeVersion,after_id)
    if not old or not new: raise HTTPException(404,'Wersja CV nie istnieje')
    if old.profile_id!=new.profile_id: raise HTTPException(422,'Wersje muszą należeć do jednego profilu')
    return {'before_id':old.id,'after_id':new.id,**compare_content(json.loads(old.content_json),json.loads(new.content_json))}

@app.post('/api/v1/resumes/{resume_id}/restore',status_code=201)
def restore_resume(resume_id: str, db: Session = Depends(get_db)):
    source=db.get(ResumeVersion,resume_id)
    if source is None: raise HTTPException(404,'Wersja CV nie istnieje')
    restored=ResumeVersion(profile_id=source.profile_id,job_id=source.job_id,
                           content_json=source.content_json,restored_from_id=source.id)
    db.add(restored);db.commit();db.refresh(restored)
    return {'id':restored.id,'restored_from_id':source.id,'created_at':restored.created_at.isoformat(),
            'content':json.loads(restored.content_json)}

# Explicitly triggered AI review, never runs during typing or ATS diagnostics.
from .ai_analysis import analyze_ai, AIUnavailable

class AIAnalysisRequest(BaseModel):
    provider: str
    consent_to_external_processing: bool = False

@app.post('/api/v1/jobs/{job_id}/ai-analysis')
def ai_review(job_id: str, payload: AIAnalysisRequest, db: Session = Depends(get_db)):
    if not payload.consent_to_external_processing:
        raise HTTPException(422, 'Explicit consent is required before sending professional data to an external AI provider.')
    job = db.get(JobPosting, job_id)
    if not job:
        raise HTTPException(404, 'Job posting not found')
    if payload.provider not in ('openai', 'anthropic'):
        raise HTTPException(422, 'Choose openai or anthropic')
    try:
        return analyze_ai(payload.provider, serialize(get_profile(db, job.profile_id)), job.description)
    except AIUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
