"""Deterministic evidence-based matching; no invented ATS score."""
import re
from collections import Counter

STOP = set('oraz oraz i lub dla na do w z ze od po jest jestesmy wymagamy wymagania doświadczenie praca pracy mile widziane znajomosc znajomość umiejętność umiejętności ability with from the and for you are our using have experience skills required preferred years team work good strong excellent must minimum min przy jako to of in a an be we is it this that your as at'.split())
CANONICAL = {'js':'javascript','ts':'typescript','postgres':'postgresql','py':'python','reactjs':'react','nodejs':'node.js','restful':'rest api','rest':'rest api','gitlab ci':'gitlab ci','k8s':'kubernetes'}
TECH = ['python','java','javascript','typescript','react','angular','vue','node.js','sql','postgresql','mysql','docker','kubernetes','aws','azure','gcp','git','linux','fastapi','django','flask','spring','rest api','graphql','html','css','excel','power bi','tableau','figma','jira','scrum','agile','c++','c#','php','go','rust','redis','mongodb','terraform','ci/cd','pytest','pandas','numpy','machine learning','analiza danych','zarządzanie projektami']

def normalize(v):
    return CANONICAL.get(v.casefold().strip(),v.casefold().strip())

def present(term, text):
    term = re.escape(term).replace(r'\ ',r'\s+')
    return bool(re.search(r'(?<![\w])'+term+r'(?![\w])',text,re.I))

def extract_requirements(description):
    found=[]
    for term in TECH:
        if present(term,description):
            found.append({'name':term,'priority':'required' if any(present(x,description[max(0,m.start()-100):m.end()+70]) for m in re.finditer(re.escape(term),description,re.I) for x in ('wymagane','required','must have','requirements')) else 'unspecified'})
    for alias,canonical in CANONICAL.items():
        if present(alias,description) and canonical not in [x['name'] for x in found]:found.append({'name':canonical,'priority':'unspecified'})
    return sorted(found,key=lambda x:x['name'])

def analyze(profile,job):
    text='\n'.join([profile.get('summary') or '',profile.get('headline') or '']+[str(x.get('description') or '')+' '+str(x.get('title') or '') for x in profile['experiences']]+[str(x.get('description') or '')+' '+str(x.get('name') or '') for x in profile['projects']])
    skills={normalize(x['name']):x for x in profile['skills']}
    items=[]
    for req in extract_requirements(job['description']):
        term=req['name']; sk=skills.get(term)
        proof = next((s.get('evidence_note') for k,s in skills.items() if k==term and s.get('evidence_note')), None)
        if not proof:
            proof = next((str(x.get('description'))[:240] for x in profile['experiences']+profile['projects'] if present(term,str(x.get('description') or ''))),None)
        if not proof and present(term,text):proof='Wzmianka w podsumowaniu lub nagłówku; potwierdź kontekst.'
        state='evidenced' if proof and ('potwierdź kontekst' not in proof) else 'mentioned' if sk or proof else 'missing'
        items.append({**req,'status':state,'evidence':proof,'suggestion': 'Dodaj konkretny, prawdziwy przykład zastosowania.' if state=='mentioned' else 'Nie dodawaj bez rzeczywistego doświadczenia.' if state=='missing' else 'Możesz wyeksponować istniejący dowód w CV.'})
    weights={'required':3,'unspecified':2,'preferred':1}
    denom=sum(weights[x['priority']] for x in items)
    points=sum(weights[x['priority']] * {'evidenced':1,'mentioned':0.5,'missing':0}[x['status']] for x in items)
    return {'requirements':items,'match_percent':round(100*points/denom) if denom else None,'metric_note':'Autorska metryka pokrycia wykrytych słów/kompetencji; nie jest oceną ATS ani prognozą zatrudnienia.','limitations':['Reguły rozpoznają ograniczony słownik terminów i nie rozumieją pełnej semantyki ogłoszenia.','Brak dowodu w CV nie oznacza braku rzeczywistej kompetencji.'],'counts':dict(Counter(x['status'] for x in items))}
