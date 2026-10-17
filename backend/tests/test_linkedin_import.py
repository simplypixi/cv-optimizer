import io
import zipfile

def archive(files):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for n,content in files.items(): z.writestr(n,content)
    return b.getvalue()

def test_preview_confirm_duplicates(client):
    pid=client.post('/api/v1/profiles',json={'full_name':'Import Test'}).json()['id']
    data=archive({'Basic_LinkedInDataExport/Positions.csv':'Company Name,Title,Started On,Finished On,Description\nACME,Junior Developer,Jan 2020,,first\nACME,Senior Developer,2022-05,,second\n','Skills.csv':'Name\nPython\nTypeScript\n','Education.csv':'School Name,Degree Name,Start Date,End Date\nTest University,MSc,2015,2020\n'})
    response=client.post(f'/api/v1/profiles/{pid}/linkedin/preview',files={'file':('linkedin.zip',data,'application/zip')})
    assert response.status_code==200,response.text
    sections=response.json()['sections']
    assert len(sections['experiences'])==2
    assert len(sections['skills'])==2
    for repeat in range(2):
        r=client.post(f'/api/v1/profiles/{pid}/linkedin/commit',json={'sections':sections})
        assert r.status_code==200,r.text
        assert r.json()['added']['skills']==(2 if repeat==0 else 0)
    profile=client.get(f'/api/v1/profiles/{pid}').json()
    assert len(profile['experiences'])==2
    assert len(profile['skills'])==2

def test_reject_invalid_zip(client):
    pid=client.post('/api/v1/profiles',json={'full_name':'Test'}).json()['id']
    r=client.post(f'/api/v1/profiles/{pid}/linkedin/preview',files={'file':('linkedin.zip',b'bad','application/zip')})
    assert r.status_code==422
