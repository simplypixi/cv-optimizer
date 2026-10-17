def make_profile(client):
    response = client.post("/api/v1/profiles", json={"full_name":"Anna Nowak", "email":"anna@example.com", "location":"Poznań"})
    assert response.status_code == 201, response.text
    return response.json()["id"]

def test_health(client):
    assert client.get("/api/v1/health").json() == {"status":"ok"}

def test_profile_crud(client):
    pid = make_profile(client)
    assert len(client.get("/api/v1/profiles").json()) == 1
    r = client.patch(f"/api/v1/profiles/{pid}", json={"headline":"Python Developer"})
    assert r.status_code == 200
    assert r.json()["headline"] == "Python Developer"
    assert client.delete(f"/api/v1/profiles/{pid}").status_code == 204
    assert client.get(f"/api/v1/profiles/{pid}").status_code == 404

def test_sections_and_skills(client):
    pid = make_profile(client)
    base=f"/api/v1/profiles/{pid}"
    experience = client.post(base+"/experiences", json={"company":"ABC", "title":"Developer", "start_date":"2023-01-01"})
    assert experience.status_code == 201, experience.text
    assert client.post(base+"/education", json={"institution":"Politechnika"}).status_code == 201
    assert client.post(base+"/projects", json={"name":"Portfolio"}).status_code == 201
    skill = client.post(base+"/skills", json={"name":"Python", "evidence_note":"Projekt ABC"})
    assert skill.status_code == 201, skill.text
    assert client.post(base+"/skills", json={"name":"Python"}).status_code == 409
    result=client.get(base).json()
    assert len(result["experiences"]) == 1
    assert len(result["education"]) == 1
    assert len(result["projects"]) == 1
    assert result["skills"][0]["name"] == "Python"
    assert client.delete(base+"/experiences/"+experience.json()["id"]).status_code == 204
    assert client.get(base).json()["experiences"] == []

def test_validation(client):
    assert client.post("/api/v1/profiles", json={"full_name":""}).status_code == 422
    pid=make_profile(client)
    assert client.patch(f"/api/v1/profiles/{pid}", json={"full_name":None}).status_code == 422
    assert client.post(f"/api/v1/profiles/{pid}/experiences", json={"company":"A", "title":"B", "start_date":"2025-01-01", "end_date":"2024-01-01"}).status_code == 422
    assert client.get("/api/v1/profiles/no-such-id").status_code == 404
