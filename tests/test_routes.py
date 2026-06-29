import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # triggers lifespan -> content load
        yield c


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_index_renders_profile_and_a_post(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "Dmytro Kostevskyi" in body
    assert "Operational Core" in body  # a known seed-post title
    # all three tabs are present in the DOM for SEO
    assert 'data-panel="posts"' in body
    assert 'data-panel="products"' in body
    assert 'data-panel="resume"' in body


def test_post_detail_renders(client):
    r = client.get("/posts/crm-operational-core")
    assert r.status_code == 200
    assert "Building a CRM That Became the Operational Core" in r.text
    assert "Start from the events" in r.text  # rendered markdown body (an h2)


def test_unknown_post_is_404(client):
    r = client.get("/posts/nope-not-here")
    assert r.status_code == 404
    assert "wandered off" in r.text


def test_unknown_route_is_404(client):
    r = client.get("/totally/unknown")
    assert r.status_code == 404


def test_resume_route(client):
    r = client.get("/resume.pdf")
    # 200 if the PDF was dropped in, 404 (styled) if not — both are valid states.
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.headers["content-type"] == "application/pdf"
