from teknologkoren_se import util

# The test app is created with config.py's SERVER_NAME, so requests are
# for host localhost.localdomain:5000.
HOST = 'http://localhost.localdomain:5000'


class TestIsSafeUrl:
    def test_relative_path_is_safe(self, app):
        with app.test_request_context('/sv/'):
            assert util.is_safe_url('/sv/konserter/') is True

    def test_absolute_url_same_host_is_safe(self, app):
        with app.test_request_context('/sv/'):
            assert util.is_safe_url(HOST + '/sv/konserter/') is True

    def test_https_url_same_host_is_safe(self, app):
        with app.test_request_context('/sv/'):
            url = 'https://localhost.localdomain:5000/sv/'
            assert util.is_safe_url(url) is True

    def test_absolute_url_other_host_is_unsafe(self, app):
        with app.test_request_context('/sv/'):
            assert util.is_safe_url('https://evil.tld/x') is False

    def test_protocol_relative_url_is_unsafe(self, app):
        # '//evil.tld' inherits the scheme but changes the host.
        with app.test_request_context('/sv/'):
            assert util.is_safe_url('//evil.tld/x') is False

    def test_javascript_scheme_is_unsafe(self, app):
        with app.test_request_context('/sv/'):
            assert util.is_safe_url('javascript:alert(1)') is False


class TestGetRedirectTarget:
    def test_returns_safe_next_argument(self, app):
        with app.test_request_context('/sv/login?next=/sv/konserter/'):
            assert util.get_redirect_target() == '/sv/konserter/'

    def test_skips_unsafe_next_argument(self, app):
        with app.test_request_context('/sv/login?next=https://evil.tld/x'):
            assert util.get_redirect_target() is None

    def test_unsafe_next_falls_back_to_safe_referrer(self, app):
        with app.test_request_context(
                '/sv/login?next=//evil.tld/x',
                headers={'Referer': HOST + '/sv/konserter/'}):
            assert util.get_redirect_target() == HOST + '/sv/konserter/'

    def test_skips_referrer_pointing_to_current_url(self, app):
        # Redirecting to the page we are on would loop.
        with app.test_request_context(
                '/sv/login',
                headers={'Referer': HOST + '/sv/login'}):
            assert util.get_redirect_target() is None

    def test_no_next_and_no_referrer_returns_none(self, app):
        with app.test_request_context('/sv/login'):
            assert util.get_redirect_target() is None


class TestUrlForFile:
    def test_joins_uploads_base_url(self, app):
        assert util.url_for_file('stamma.pdf') == \
            '/static/uploads/files/stamma.pdf'


class TestUrlForImage:
    # config.py has DEBUG = True and the test config does not override
    # it, so the app fixture is in debug mode. monkeypatch restores the
    # session-scoped app's config after each test.
    def test_without_width(self, app):
        assert util.url_for_image('foo.jpg') == \
            '/static/uploads/images/foo.jpg'

    def test_width_in_debug_mode_is_ignored(self, app, monkeypatch):
        # Flask's dev server can't serve nginx's resize paths, so debug
        # mode links straight to the original image.
        monkeypatch.setitem(app.config, 'DEBUG', True)
        assert util.url_for_image('foo.jpg', width=300) == \
            '/static/uploads/images/foo.jpg'

    def test_width_outside_debug_mode_prefixes_path(self, app, monkeypatch):
        monkeypatch.setitem(app.config, 'DEBUG', False)
        assert util.url_for_image('foo.jpg', width=300) == \
            '/static/uploads/images/img300/foo.jpg'

    def test_no_width_outside_debug_mode(self, app, monkeypatch):
        monkeypatch.setitem(app.config, 'DEBUG', False)
        assert util.url_for_image('foo.jpg') == \
            '/static/uploads/images/foo.jpg'


class TestUrlForOtherPage:
    def test_from_frontpage(self, app):
        with app.test_request_context('/sv/'):
            assert util.url_for_other_page(3) == '/sv/blogg/sida/3'

    def test_from_paginated_page(self, app):
        with app.test_request_context('/sv/blogg/sida/2'):
            assert util.url_for_other_page(5) == '/sv/blogg/sida/5'

    def test_keeps_other_view_args(self, app):
        # The language code from the path is a view arg too.
        with app.test_request_context('/en/blogg/sida/2'):
            assert util.url_for_other_page(3) == '/en/blogg/sida/3'

    def test_events_endpoint(self, app):
        with app.test_request_context('/sv/konserter/'):
            assert util.url_for_other_page(2) == '/sv/konserter/sida/2'
