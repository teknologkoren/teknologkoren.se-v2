import pytest

from teknologkoren_se import factory, models

# Base config shared by all test apps. Individual tests that need other
# settings should monkeypatch app.config instead of creating a new app
# (see _app below for why).
BASE_TEST_CONFIG = {
    # In-memory database: fast, and every test starts from a known state.
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    # Forms are tested without CSRF tokens.
    'WTF_CSRF_ENABLED': False,
    'TESTING': True,
}


@pytest.fixture(scope='session')
def _app(tmp_path_factory):
    """The Flask app, created once per test session.

    create_app() cannot be called twice in one process: register_blueprints()
    calls public.init_dynamic_pages(), which adds url rules to the
    module-level blueprint object after it has been registered, and Flask
    rejects that on the second call. One shared app plus a per-test database
    reset (see `app`) works around this, and is faster anyway.
    """
    config = {
        **BASE_TEST_CONFIG,
        # Keep test uploads out of the repository's static directory.
        'UPLOADS_DEFAULT_DEST': str(tmp_path_factory.mktemp('uploads')),
    }
    return factory.create_app(config=config)


@pytest.fixture
def app(_app):
    """The session app with a fresh, seeded database for every test.

    The database is seeded like `flask initdb` would: the four static
    pages and the Config row, which public views assume exist.

    Caveat: because this fixture keeps an app context pushed for the whole
    test, the test client reuses it across requests (a fresh test_client
    does too), so `flask.g` set by one request is still visible in the
    next — unlike production, where every request gets a fresh g. Tests
    exercising g-dependent behavior (e.g. the lang-code redirect) must
    clear the leaked keys between requests; see fresh_g() in
    tests/locale_test.py.
    """
    with _app.app_context():
        models.db.drop_all()
        factory.init_db(_app)
        yield _app
        models.db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
