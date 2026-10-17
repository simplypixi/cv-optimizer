from app.documents import render_resume
from app.ats_diagnostics import diagnose

SAMPLE = {'full_name':'Anna Nowak','email':'anna@example.org','subtitle':'Software Engineer','summary':'Pracuję z Pythonem, API i relacyjnymi bazami danych od kilku lat.', 'experiences':[{'title':'Developer','company':'Example Ltd','start_date':'2022-01','end_date':None,'description':'Projektowanie API, testowanie oraz utrzymanie aplikacji Python.'}], 'template':'editorial'}

def test_profiles_have_explainable_scores():
    result=diagnose(render_resume(SAMPLE))
    assert set(result['profiles'])=={'greenhouse','workday','lever'}
    for p in result['profiles'].values():
        assert 0<=p['score']<=100
        assert p['coverage']<100
        assert any(x['status']=='unknown' for x in p['rules'])
        assert p['source'].startswith('https://')

def test_checks_change_for_problematic_document():
    good=diagnose(render_resume(SAMPLE))
    bad=diagnose(render_resume({'full_name':'X','template':'classic'}))
    assert good['profiles']['greenhouse']['score'] > bad['profiles']['greenhouse']['score']
    assert any(c['id']=='contact' and c['status']=='warn' for c in bad['document_checks'])

def test_mock_pdf_does_not_pass_roundtrip():
    result=diagnose(render_resume(SAMPLE), b'%PDF-1.4 invalid')
    assert result['pdf_checked'] is True
    assert next(x for x in result['document_checks'] if x['id']=='pdf')['status']=='fail'

def test_manual_endpoint(client):
    p=client.post('/api/v1/profiles',json={'full_name':'Anna Nowak','email':'anna@example.org'}).json()
    r=client.post('/api/v1/resumes',json={'profile_id':p['id'],'content':SAMPLE})
    assert r.status_code==201, r.text
    response=client.post(f"/api/v1/resumes/{r.json()['id']}/ats-check?format=docx")
    assert response.status_code==200, response.text
    assert response.json()['profiles']['greenhouse']['score'] is not None
    assert response.json()['pdf_checked'] is False
    assert client.post('/api/v1/resumes/not-found/ats-check').status_code==404
