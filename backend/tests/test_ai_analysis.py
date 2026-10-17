from app.ai_analysis import professional_payload, analyze_ai

def test_omits_direct_personal_information():
    payload = professional_payload({'full_name':'SECRET NAME','email':'secret@example.com','phone':'555111','location':'Secret Town', 'links':[{'url':'https://example.org/private'}], 'skills':[{'name':'Python','evidence_note':'Built APIs'}]},'Python role')
    assert 'SECRET NAME' not in str(payload)
    assert 'secret@example.com' not in str(payload)
    assert '555111' not in str(payload)
    assert payload['skills'][0]['name'] == 'Python'

def test_requires_consent_and_api_key(client, monkeypatch):
    p=client.post('/api/v1/profiles',json={'full_name':'Tester'}).json()
    j=client.post('/api/v1/jobs',json={'profile_id':p['id'],'title':'Developer','description':'Python developer'}).json()
    route=f"/api/v1/jobs/{j['id']}/ai-analysis"
    assert client.post(route,json={'provider':'openai'}).status_code == 422
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    response=client.post(route,json={'provider':'openai','consent_to_external_processing':True})
    assert response.status_code == 503
    assert 'OPENAI_API_KEY' in response.json()['detail']

def test_mock_ai_provider_response(monkeypatch):
    from app import ai_analysis
    monkeypatch.setenv('OPENAI_API_KEY','test-placeholder')
    monkeypatch.setattr(ai_analysis,'_message', lambda *args: {'overview':'Good foundation','strengths':['Python'], 'gaps':[], 'suggestions':[{'section':'summary','current':'Developer','proposed':'Python developer','reason':'Relevant','evidence':'Python experience'}]})
    response=analyze_ai('openai',{'skills':[{'name':'Python'}]},'Python role')
    assert response['analysis']['overview']=='Good foundation'
    assert response['analysis']['suggestions'][0]['proposed']=='Python developer'
