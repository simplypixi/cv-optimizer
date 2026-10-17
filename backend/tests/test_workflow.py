from io import BytesIO
from docx import Document
from fastapi.testclient import TestClient
from app.main import app

def test_complete_workflow(client):
    profile=client.post('/api/v1/profiles',json={'full_name':'Anna Nowak','email':'anna@example.com'}).json()
    pid=profile['id']
    s=client.post(f'/api/v1/profiles/{pid}/skills',json={'name':'Python','evidence_note':'Tworzyłam aplikacje w Pythonie'})
    assert s.status_code==201
    offer=client.post('/api/v1/jobs',json={'profile_id':pid,'title':'Developer','description':'Required Python and Docker'});assert offer.status_code==201
    report=client.get(f'/api/v1/jobs/{offer.json()["id"]}/analysis').json()
    assert report['counts']=={'missing':1,'evidenced':1}
    assert report['match_percent']==50
    payload=client.get(f'/api/v1/profiles/{pid}').json()
    version=client.post('/api/v1/resumes',json={'profile_id':pid,'job_id':offer.json()['id'],'content':payload})
    assert version.status_code==201
    v=version.json()['id']
    assert client.get(f'/api/v1/resumes/{v}/export?format=docx').content.startswith(b'PK')
    assert client.get(f'/api/v1/resumes/{v}/export?format=pdf').content.startswith(b'%PDF')
    assert client.get(f'/api/v1/resumes/{v}/lint').status_code==200
    assert len(client.get(f'/api/v1/profiles/{pid}/resumes').json())==1

def test_document_import(client):
    doc=Document();doc.add_paragraph('Anna Nowak anna@example.com - Python developer')
    buf=BytesIO();doc.save(buf)
    response=client.post('/api/v1/documents/import',files={'file':('cv.docx',buf.getvalue(),'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
    assert response.status_code==200
    assert 'Anna Nowak' in response.json()['text']
    assert client.post('/api/v1/documents/import',files={'file':('bad.exe',b'test')}).status_code==422
