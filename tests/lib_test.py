import hashlib
import pathlib
import re

import flask
import markdown

from teknologkoren_se.lib import mdx_headdown


# mdx_headdown

def headdown(text, **kwargs):
    """Render markdown with the headdown extension.

    Passing an extension instance (rather than its import path string)
    sidesteps Python-Markdown's config lookup by name.
    """
    return markdown.markdown(
        text, extensions=[mdx_headdown.makeExtension(**kwargs)]
    )


def test_default_offset_downgrades_one_level():
    assert headdown('# Rubrik') == '<h2>Rubrik</h2>'


def test_offset_two_downgrades_two_levels():
    assert headdown('# A\n\n## B', offset=2) == '<h3>A</h3>\n<h4>B</h4>'


def test_offset_zero_keeps_headings():
    assert headdown('# Rubrik', offset=0) == '<h1>Rubrik</h1>'


def test_downgrade_caps_at_h6():
    assert headdown('###### Rubrik') == '<h6>Rubrik</h6>'


def test_large_offset_caps_at_h6():
    assert headdown('## Rubrik', offset=10) == '<h6>Rubrik</h6>'


def test_negative_offset_is_absolutised():
    assert headdown('# Rubrik', offset=-2) == '<h3>Rubrik</h3>'


def test_non_headings_are_untouched():
    assert headdown('bara text') == '<p>bara text</p>'


# cache_bust

STATIC_FILE = 'css/style.css'


def static_file_bytes(app):
    return pathlib.Path(app.static_folder, STATIC_FILE).read_bytes()


def busted_url(app):
    with app.test_request_context('/sv/'):
        return flask.url_for('static', filename=STATIC_FILE)


def test_static_url_gets_hashed_prefix(app):
    assert re.fullmatch(
        r'/static/c[0-9a-f]{7}/' + re.escape(STATIC_FILE), busted_url(app)
    )


def test_hash_is_derived_from_file_content(app):
    md5 = hashlib.md5(static_file_bytes(app)).hexdigest()
    assert busted_url(app) == '/static/c{}/{}'.format(md5[:7], STATIC_FILE)


def test_busted_url_serves_the_file(app, client):
    response = client.get(busted_url(app))
    assert response.status_code == 200
    assert response.data == static_file_bytes(app)


def test_unbusted_url_still_serves_the_file(app, client):
    response = client.get('/static/' + STATIC_FILE)
    assert response.status_code == 200
    assert response.data == static_file_bytes(app)


def test_unknown_filename_passes_through_unbusted(app):
    with app.test_request_context('/sv/'):
        url = flask.url_for('static', filename='does-not-exist.css')
    assert url == '/static/does-not-exist.css'


def test_unknown_filename_404s(client):
    assert client.get('/static/does-not-exist.css').status_code == 404
