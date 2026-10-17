from app.models import ATSReport

def test_report_history_compare_restore(client):
    p=client.post('/api/v1/profiles',json={'full_name':'Test Candidate','email':'candidate@example.com'}).json()
    base={'full_name':'Test Candidate','email':'candidate@example.com','experiences':[{'company':'Acme','title':'Engineer','start_date':'2021-01-01','description':'Created Python services'}], 'summary':'I developed reliable systems with measurable results in Python and SQL.'}
    v1=client.post('/api/v1/resumes',json={'profile_id':p['id'],'content':base}).json()['id']
    modified={**base,'summary':'Improved systems with measured performance; 2022 to 2024.'}
    v2=client.post('/api/v1/resumes',json={'profile_id':p['id'],'content':modified}).json()['id']
    for rid in (v1,v2):
        result=client.post(f'/api/v1/resumes/{rid}/ats-check?format=docx')
        assert result.status_code==200, result.text
    history=client.get(f'/api/v1/profiles/{p["id"]}/ats-history').json()
    assert len(history)==2
    a=next(x for x in history if x['resume_id']==v1)
    b=next(x for x in history if x['resume_id']==v2)
    compare=client.get('/api/v1/ats-reports/compare',params={'before_id':a['id'],'after_id':b['id']})
    assert compare.status_code==200 and set(compare.json()['profiles'])=={'greenhouse','workday','lever'}
    restore=client.post(f'/api/v1/resumes/{v1}/restore')
    assert restore.status_code==201
    assert restore.json()['id'] not in [v1,v2]
    assert restore.json()['restored_from_id']==v1
    versions=client.get(f'/api/v1/profiles/{p["id"]}/resumes').json()
    assert len(versions)==3
    assert next(x for x in versions if x['id']==restore.json()['id'])['content']==base
    assert len(client.get(f'/api/v1/profiles/{p["id"]}/ats-history').json())==2
    assert client.get('/api/v1/ats-reports/compare',params={'before_id':a['id'],'after_id':'invalid'}).status_code==404
