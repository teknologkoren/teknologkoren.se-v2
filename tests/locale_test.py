import flask

from teknologkoren_se import locale

# The app and client pytest fixtures live in tests/conftest.py, where pytest
# picks them up automatically without imports.


class TestLangCodeThroughClient:
    def test_sv_prefix_sets_session_lang(self, client):
        response = client.get('/sv/')
        assert response.status_code == 200

        with client.session_transaction() as session:
            assert session['lang_code'] == 'sv'

    def test_en_prefix_sets_session_lang(self, client):
        response = client.get('/en/')
        assert response.status_code == 200

        with client.session_transaction() as session:
            assert session['lang_code'] == 'en'

    def test_root_redirects_to_en_with_english_accept_language(self, client):
        response = client.get('/', headers={'Accept-Language': 'en'})
        assert response.status_code == 302

        response = client.get('/', headers={'Accept-Language': 'en'},
                              follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/en/'

    def test_root_redirects_to_sv_by_default(self, client):
        # No Accept-Language header at all: Swedish is the fallback.
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/sv/'

    def test_root_redirects_to_sv_with_unsupported_accept_language(
            self, client):
        response = client.get('/', headers={'Accept-Language': 'de'},
                              follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/sv/'

    @staticmethod
    def fresh_g():
        """Clear the lang code that leaked into flask.g.

        The app fixture keeps one app context pushed for the whole
        test, and Flask reuses an already-pushed app context for client
        requests, so g.lang_code set during one request survives into
        the next. In production every request has its own g. Popping
        the leaked value restores production behavior for the next
        request.
        """
        flask.g.pop('lang_code', None)

    def test_bare_path_redirects_using_session_lang_en(self, client):
        client.get('/en/')

        self.fresh_g()
        response = client.get('/kontakt')
        assert response.status_code == 302

        self.fresh_g()
        response = client.get('/kontakt', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/en/kontakt'

    def test_bare_path_redirects_using_session_lang_sv(self, client):
        client.get('/sv/')

        self.fresh_g()
        response = client.get('/kontakt', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/sv/kontakt'

    def test_session_lang_survives_language_switch(self, client):
        # Last visited language prefix wins.
        client.get('/sv/')
        client.get('/en/')

        self.fresh_g()
        response = client.get('/kontakt', follow_redirects=True)
        assert response.request.path == '/en/kontakt'

    def test_invalid_lang_prefix_404s(self, client):
        # 'de' is not a valid lang code, and prepending a lang code to
        # '/de/kontakt' does not produce a matching route either, so the
        # request falls through to a 404 rather than a redirect.
        response = client.get('/de/kontakt')
        assert response.status_code == 404

    def test_nonexistent_bare_path_404s(self, client):
        # No lang code and no route even with one prepended.
        response = client.get('/finns-inte')
        assert response.status_code == 404


class TestGetLocale:
    def test_g_lang_code_wins(self, app):
        with app.test_request_context('/'):
            flask.g.lang_code = 'en'
            flask.session['lang_code'] = 'sv'
            assert locale.get_locale() == 'en'

    def test_session_lang_code_when_no_g(self, app):
        with app.test_request_context('/'):
            flask.session['lang_code'] = 'en'
            assert locale.get_locale() == 'en'

    def test_accept_language_when_no_g_or_session(self, app):
        with app.test_request_context(
                '/', headers={'Accept-Language': 'de,en;q=0.8'}):
            assert locale.get_locale() == 'en'

    def test_default_sv_when_nothing_matches(self, app):
        with app.test_request_context('/', headers={'Accept-Language': 'de'}):
            assert locale.get_locale() == 'sv'


class TestGetString:
    def test_swedish_translation(self, app):
        with app.test_request_context('/'):
            flask.g.lang_code = 'sv'
            assert (locale.get_string('wrong-login')
                    == 'Fel användarnamn eller lösenord.')

    def test_english_translation(self, app):
        with app.test_request_context('/'):
            flask.g.lang_code = 'en'
            assert (locale.get_string('wrong-login')
                    == 'Wrong username or password.')

    def test_unknown_key_falls_back_to_key(self, app):
        with app.test_request_context('/'):
            flask.g.lang_code = 'sv'
            assert locale.get_string('no-such-key') == 'no-such-key'

    def test_unknown_key_falls_back_to_key_even_when_lazy(self, app):
        # No translation entry: the key itself is returned, not a
        # LazyTranslation.
        with app.test_request_context('/'):
            assert locale.get_string('no-such-key', lazy=True) == 'no-such-key'


class TestLazyTranslation:
    def test_get_string_lazy_returns_lazy_object(self):
        # No app or request context needed to *create* it.
        lazy = locale.get_string('wrong-login', lazy=True)
        assert isinstance(lazy, locale.LazyTranslation)

    def test_resolves_at_str_time_per_locale(self, app):
        # One and the same object renders differently depending on the
        # locale at the time str() is called.
        lazy = locale.get_string('wrong-login', lazy=True)

        with app.test_request_context('/'):
            flask.g.lang_code = 'sv'
            assert str(lazy) == 'Fel användarnamn eller lösenord.'

        with app.test_request_context('/'):
            flask.g.lang_code = 'en'
            assert str(lazy) == 'Wrong username or password.'
