from io import BytesIO
from docx import Document
from app.documents import render_resume, _experience_groups

def sample():
    return {'full_name':'Anna Nowak','email':'anna@example.com','experiences':[
        {'company':'Alfa SA','title':'Junior','start_date':'2021-01-01','end_date':'2022-12-31','description':'Pierwsze stanowisko'},
        {'company':' ALFA  SA ','title':'Senior','start_date':'2023-01-01','end_date':None,'description':'Awans i prowadzenie projektów'},
        {'company':'Beta','title':'Konsultant','start_date':'2020-01-01','end_date':'2020-12-31','description':'Projekt'}], 'skills':[{'name':'Python'}]}

def test_all_templates_and_career_path():
    for template in ['classic','modern','compact']:
        for group in [True,False]:
            raw=render_resume({**sample(),'template':template,'career_path':group})
            doc=Document(BytesIO(raw))
            txt='\n'.join(x.text for x in doc.paragraphs)
            assert 'Senior' in txt and 'Junior' in txt and 'Konsultant' in txt
            assert 'Pierwsze stanowisko' in txt and 'Awans' in txt
            assert ('Senior —' not in txt) if group else ('Senior —' in txt)

def test_grouping_maintains_original_roles():
    items=sample()['experiences']
    output=_experience_groups(items,True)
    assert len(output)==2
    assert len(output[0]['roles'])==2
    assert len(items)==3

def test_resume_endpoint_preserves_preferences(client):
    p=client.post('/api/v1/profiles',json={'full_name':'Anna Nowak'}).json()
    body={'profile_id':p['id'],'content':{**sample(),'template':'modern','career_path':True}}
    response=client.post('/api/v1/resumes',json=body)
    assert response.status_code==201,response.text
    versions=client.get(f"/api/v1/profiles/{p['id']}/resumes").json()
    assert versions[0]['content']['career_path'] is True
    assert versions[0]['content']['template']=='modern'
    assert client.get(f"/api/v1/resumes/{response.json()['id']}/export?format=docx").status_code==200
