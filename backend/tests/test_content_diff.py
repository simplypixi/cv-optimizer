def test_content_diff_and_restore(client):
    profile=client.post('/api/v1/profiles',json={'full_name':'Candidate','email':'person@example.com'}).json()
    base={'full_name':'Candidate','summary':'Python developer','skills':[{'name':'Python'}]}
    newer={'full_name':'Candidate','summary':'Python and SQL developer','skills':[{'name':'Python'},{'name':'SQL'}]}
    a=client.post('/api/v1/resumes',json={'profile_id':profile['id'],'content':base}).json()['id']
    b=client.post('/api/v1/resumes',json={'profile_id':profile['id'],'content':newer}).json()['id']
    r=client.get('/api/v1/resumes/compare-content',params={'before_id':a,'after_id':b})
    assert r.status_code==200,r.text
    diff=r.json()
    assert diff['counts']['changed']>=1 and diff['counts']['added']>=1
    assert any('summary' in x['path'].lower() or 'Podsumowanie' in x['path'] for x in diff['changes'])
    assert client.get('/api/v1/resumes/compare-content',params={'before_id':a,'after_id':'bad'}).status_code==404
    restored=client.post(f'/api/v1/resumes/{a}/restore').json()
    assert restored['id']!=a
    zero=client.get('/api/v1/resumes/compare-content',params={'before_id':a,'after_id':restored['id']}).json()
    assert zero['changes']==[]

def test_diff_rejects_other_profiles(client):
    ids=[]
    for i in range(2):
        p=client.post('/api/v1/profiles',json={'full_name':f'Candidate {i}'}).json()
        ids.append(client.post('/api/v1/resumes',json={'profile_id':p['id'],'content':{'full_name':f'Candidate {i}'}}).json()['id'])
    assert client.get('/api/v1/resumes/compare-content',params={'before_id':ids[0],'after_id':ids[1]}).status_code==422
