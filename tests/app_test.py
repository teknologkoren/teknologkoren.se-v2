from tests import helpers


def test_frontpage(client):
    response = client.get('/sv/')
    assert response.status_code == 200


def test_frontpage_english(client):
    response = client.get('/en/')
    assert response.status_code == 200


def test_missing_lang_code_redirects(client):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path in ('/sv/', '/en/')


def test_frontpage_shows_post(client):
    helpers.make_blogpost(title_sv='Julkonsert i Storkyrkan')
    response = client.get('/sv/')
    assert 'Julkonsert i Storkyrkan' in response.get_data(as_text=True)
