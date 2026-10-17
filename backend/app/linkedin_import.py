"""Safe, explicit import from LinkedIn's user-requested data archive.
No API credentials, network, scraping, or execution of uploaded files.
"""
import csv
import io
import re
import zipfile
from datetime import date, datetime
from pathlib import PurePosixPath

MAX_ARCHIVE = 15_000_000
MAX_MEMBER = 3_000_000
MAX_TOTAL = 22_000_000


def norm(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').casefold())


def field(row, *names):
    normalized = {norm(k): (v or '').strip() for k, v in row.items() if k}
    return next((normalized[norm(name)] for name in names if normalized.get(norm(name))), '')


def parse_date(value):
    value = str(value or '').strip()
    if not value or value.lower() in ('present', 'current', 'obecnie'): return None
    for fmt in ('%b %Y', '%B %Y', '%b %d, %Y', '%B %d, %Y'):
        try:
            parsed = datetime.strptime(value,fmt)
            return date(parsed.year, parsed.month, 1).isoformat()
        except ValueError: pass
    formats = [r'^(\d{4})-(\d{1,2})(?:-\d{1,2})?$', r'^(\d{1,2})/(\d{4})$', r'^(\d{4})$']
    for idx, pattern in enumerate(formats):
        match = re.match(pattern, value)
        if match:
            parts = [int(x) for x in match.groups()]
            try:
                return date(parts[1], parts[0], 1).isoformat() if idx == 1 else date(parts[0], parts[1] if len(parts)>1 else 1, 1).isoformat()
            except ValueError: return None
    return None


def csv_rows(data):
    for encoding in ('utf-8-sig','utf-16','cp1252'):
        try:
            text = data.decode(encoding)
            reader = csv.DictReader(io.StringIO(text))
            if not reader.fieldnames: return []
            return list(reader)[:5000]
        except (UnicodeError, csv.Error): continue
    return []


def read_archive(data):
    if len(data) > MAX_ARCHIVE: raise ValueError('Archiwum przekracza 15 MB')
    if not zipfile.is_zipfile(io.BytesIO(data)): raise ValueError('Wymagane archiwum ZIP z LinkedIn')
    sections = {'experiences': [], 'education': [], 'skills': [], 'projects': []}
    warnings = []
    found = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > 300: raise ValueError('Zbyt dużo plików w archiwum')
        if sum(m.file_size for m in members) > MAX_TOTAL: raise ValueError('Archiwum zawiera zbyt dużo danych po rozpakowaniu')
        for info in members:
            if info.is_dir(): continue
            path = PurePosixPath(info.filename.replace('\\','/'))
            if '..' in path.parts or info.file_size > MAX_MEMBER: continue
            name = norm(path.stem)
            kind = {'positions':'experiences','experience':'experiences','education':'education','skills':'skills','projects':'projects'}.get(name)
            if not kind or path.suffix.lower() != '.csv': continue
            found.append(path.name)
            rows = csv_rows(archive.read(info))
            for row in rows:
                if kind == 'experiences':
                    company = field(row,'Company Name','Company','Organization')[:200]
                    title = field(row,'Title','Position','Role')[:200]
                    start = parse_date(field(row,'Started On','Start Date','Date Started'))
                    if not (company and title and start):
                        warnings.append(f'Pominięto wpis stanowiska (brak firmy, roli lub poprawnej daty): {title or company or "brak nazwy"}')
                        continue
                    sections[kind].append({'company':company,'title':title,'start_date':start,'end_date':parse_date(field(row,'Finished On','End Date','Date Finished')),'description':field(row,'Description') or None})
                elif kind == 'education':
                    institution = field(row,'School Name','School','Institution')[:200]
                    if not institution: continue
                    sections[kind].append({'institution':institution,'degree':field(row,'Degree Name','Degree','Field Of Study')[:200] or None,'start_date':parse_date(field(row,'Start Date','Started On')),'end_date':parse_date(field(row,'End Date','Finished On')),'description':field(row,'Notes','Activities and Societies','Description') or None})
                elif kind == 'skills':
                    name = field(row,'Name','Skill Name','Skill')[:120]
                    if name: sections[kind].append({'name':name,'category':None,'evidence_note':None})
                elif kind == 'projects':
                    name = field(row,'Title','Name','Project Name')[:200]
                    if name: sections[kind].append({'name':name,'description':field(row,'Description') or None,'url':None})
    if not found: warnings.append('Nie znaleziono obsługiwanych plików CSV: Positions, Education, Skills, Projects.')
    return {'sections':sections,'files':found,'warnings':warnings}


def fingerprint(kind, row):
    if kind=='experiences': return (norm(row['company']),norm(row['title']),row.get('start_date'))
    if kind=='education': return (norm(row['institution']),norm(row.get('degree')),row.get('start_date'))
    if kind=='projects': return (norm(row['name']),)
    return (norm(row['name']),)
