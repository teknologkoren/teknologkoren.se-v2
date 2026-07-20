import flask
import pytest
import werkzeug.exceptions

from tests import helpers
from teknologkoren_se import models


def set_lang(lang):
    """Control what locale.get_locale() returns.

    get_locale() checks flask.g first. The app fixture pushes a fresh
    app context for every test, so this never leaks between tests.
    """
    flask.g.lang_code = lang


# Post language fallback

def test_post_title_swedish(app):
    post = helpers.make_blogpost(title_sv='Hej', title_en='Hello')
    set_lang('sv')
    assert post.title() == 'Hej'


def test_post_title_english(app):
    post = helpers.make_blogpost(title_sv='Hej', title_en='Hello')
    set_lang('en')
    assert post.title() == 'Hello'


def test_post_title_english_falls_back_to_swedish(app):
    post = helpers.make_blogpost(title_sv='Hej', title_en=None)
    set_lang('en')
    assert post.title() == 'Hej'


def test_post_title_unknown_lang_aborts(app):
    post = helpers.make_blogpost()
    set_lang('de')
    with pytest.raises(werkzeug.exceptions.InternalServerError):
        post.title()


def test_post_text_english(app):
    post = helpers.make_blogpost(text_sv='Hejsan!', text_en='Hi there!')
    set_lang('en')
    assert post.text() == 'Hi there!'


def test_post_text_english_falls_back_to_swedish(app):
    post = helpers.make_blogpost(text_sv='Hejsan!', text_en=None)
    set_lang('en')
    assert post.text() == 'Hejsan!'


def test_post_slug_english(app):
    post = helpers.make_blogpost(title_sv='Ett inlägg', title_en='A post')
    set_lang('en')
    assert post.slug() == 'a-post'


def test_post_slug_english_falls_back_to_swedish(app):
    post = helpers.make_blogpost(title_sv='Ett inlägg', title_en=None)
    set_lang('en')
    assert post.slug() == 'ett-inlagg'


def test_locale_can_come_from_session(app):
    # Without g.lang_code, get_locale() falls back to the session.
    post = helpers.make_blogpost(title_sv='Hej', title_en='Hello')
    with app.test_request_context('/'):
        flask.session['lang_code'] = 'en'
        assert post.title() == 'Hello'


# Event language fallback

def test_event_location_swedish(app):
    event = helpers.make_event(location_sv='Nya Matsalen',
                               location_en='The New Dining Hall')
    set_lang('sv')
    assert event.location() == 'Nya Matsalen'


def test_event_location_english(app):
    event = helpers.make_event(location_sv='Nya Matsalen',
                               location_en='The New Dining Hall')
    set_lang('en')
    assert event.location() == 'The New Dining Hall'


def test_event_location_english_falls_back_to_swedish(app):
    event = helpers.make_event(location_sv='Nya Matsalen', location_en=None)
    set_lang('en')
    assert event.location() == 'Nya Matsalen'


def test_event_time_text_english(app):
    event = helpers.make_event(time_text_sv='Klockan 19',
                               time_text_en='7 pm')
    set_lang('en')
    assert event.time_text() == '7 pm'


def test_event_time_text_english_falls_back_to_swedish(app):
    event = helpers.make_event(time_text_sv='Klockan 19', time_text_en=None)
    set_lang('en')
    assert event.time_text() == 'Klockan 19'


# Page language fallback

def get_page(path='om-oss'):
    return models.Page.query.filter_by(path=path).one()


def test_page_text_swedish(app):
    page = get_page()
    page.text_sv = 'Om oss.'
    page.text_en = 'About us.'
    set_lang('sv')
    assert page.text() == 'Om oss.'


def test_page_text_english(app):
    page = get_page()
    page.text_sv = 'Om oss.'
    page.text_en = 'About us.'
    set_lang('en')
    assert page.text() == 'About us.'


def test_page_empty_english_text_falls_back_to_swedish(app):
    # Page.text_en is not nullable, but the empty string (which the
    # seeded pages have) is falsy and also falls back.
    page = get_page()
    page.text_sv = 'Om oss.'
    page.text_en = ''
    set_lang('en')
    assert page.text() == 'Om oss.'


def test_page_title_swedish(app):
    set_lang('sv')
    assert get_page().title() == 'Om oss'


def test_page_title_english(app):
    set_lang('en')
    assert get_page().title() == 'About us'


# Config.flash

def test_config_flash_defaults_to_none(app):
    config = models.Config.query.one()
    set_lang('sv')
    assert config.flash() is None


def test_config_flash_swedish(app):
    config = models.Config.query.one()
    config.flash_sv = 'Inställd!'
    config.flash_en = 'Cancelled!'
    set_lang('sv')
    assert config.flash() == 'Inställd!'


def test_config_flash_english_falls_back_to_swedish(app):
    config = models.Config.query.one()
    config.flash_sv = 'Inställd!'
    config.flash_en = None
    set_lang('en')
    assert config.flash() == 'Inställd!'


def test_config_flash_swedish_falls_back_to_english(app):
    # Unlike the Post accessors, flash falls back in both directions.
    config = models.Config.query.one()
    config.flash_sv = None
    config.flash_en = 'Cancelled!'
    set_lang('sv')
    assert config.flash() == 'Cancelled!'


# Slug generation ('set' event listeners)

def test_title_sv_generates_slug_sv(app):
    post = helpers.make_blogpost(title_sv='Ett inlägg')
    assert post.slug_sv == 'ett-inlagg'


def test_changing_title_sv_updates_slug_sv(app):
    post = helpers.make_blogpost(title_sv='Ett inlägg')
    post.title_sv = 'Något annat'
    assert post.slug_sv == 'nagot-annat'


def test_title_en_generates_slug_en(app):
    post = helpers.make_blogpost(title_en='A Post!')
    assert post.slug_en == 'a-post'


def test_clearing_title_en_clears_slug_en(app):
    post = helpers.make_blogpost(title_en='A Post!')
    post.title_en = None
    assert post.slug_en is None


def test_event_titles_also_generate_slugs(app):
    # The listeners are registered with propagate=True, so they fire
    # for Post's subclasses too.
    event = helpers.make_event(title_sv='En konsert')
    assert event.slug_sv == 'en-konsert'


# Markdown rendering

def test_post_html_renders_markdown(app):
    post = helpers.make_blogpost(text_sv='Hej *du*!')
    set_lang('sv')
    assert '<em>du</em>' in post.html()


def test_post_html_nl2br(app):
    post = helpers.make_blogpost(text_sv='rad ett\nrad två')
    set_lang('sv')
    assert '<br' in post.html()


def test_post_html_linkify(app):
    post = helpers.make_blogpost(text_sv='Se https://example.com idag')
    set_lang('sv')
    assert '<a href="https://example.com"' in post.html()


def test_post_html_downgrades_headings_one_level(app):
    # Note: h1 -> h2 here is a consequence of the config-key bug pinned
    # by the xfail below — the offset never reaches the extension, so its
    # default of 1 always applies, even for the default offset=0 call.
    # If the bug is fixed such that offset=0 keeps h1, update this test
    # together with removing the xfail.
    post = helpers.make_blogpost(text_sv='# Rubrik')
    set_lang('sv')
    assert '<h2>Rubrik</h2>' in post.html()


@pytest.mark.xfail(
    reason="Post.html() keys extension_configs with 'mdx_headdown' but "
           "registers the extension as 'teknologkoren_se.lib.mdx_headdown'; "
           "Python-Markdown looks configs up by the registered name, so the "
           "offset argument is silently ignored and the extension default "
           "(1) is always used.",
    strict=True,
)
def test_post_html_offset_reaches_headdown(app):
    post = helpers.make_blogpost(text_sv='# Rubrik')
    set_lang('sv')
    assert '<h3>Rubrik</h3>' in post.html(offset=2)


def test_event_time_html_renders_markdown(app):
    event = helpers.make_event(time_text_sv='Dörrarna öppnar **18:30**')
    set_lang('sv')
    assert '<strong>18:30</strong>' in event.time_html()


def test_page_html_keeps_heading_level(app):
    # Page.html() does not use the headdown extension.
    page = get_page()
    page.text_sv = '# Om oss'
    set_lang('sv')
    assert '<h1>Om oss</h1>' in page.html()


# Contact.formatted_phone

def test_phone_without_country_code_assumes_sweden():
    contact = models.Contact(phone='0707123456')
    assert contact.formatted_phone() == '+46 70 712 34 56'


def test_phone_with_separators():
    contact = models.Contact(phone='070-712 34 56')
    assert contact.formatted_phone() == '+46 70 712 34 56'


def test_phone_with_country_code():
    contact = models.Contact(phone='+46 70 712 34 56')
    assert contact.formatted_phone() == '+46 70 712 34 56'


def test_foreign_phone_keeps_country_code():
    contact = models.Contact(phone='+18005551234')
    assert contact.formatted_phone() == '+1 800-555-1234'


def test_unparsable_phone_returns_none():
    contact = models.Contact(phone='not a number')
    assert contact.formatted_phone() is None


def test_invalid_phone_returns_none():
    # '123' parses with region SE but is not a valid number.
    contact = models.Contact(phone='123')
    assert contact.formatted_phone() is None


# AdminUser passwords

def test_password_is_stored_as_bcrypt_hash(app):
    user = helpers.make_admin(password='spamspamspam')
    assert user.password != 'spamspamspam'
    assert user.password.startswith('$2b$')


def test_verify_password(app):
    user = helpers.make_admin(password='spamspamspam')
    assert user.verify_password('spamspamspam') is True
    assert user.verify_password('eggseggseggs') is False


def test_password_longer_than_72_bytes_works(app):
    """bcrypt only considers 72 bytes; longer must not raise.

    bcrypt 4.x truncated silently, 5.x raises ValueError. AdminUser
    truncates explicitly to stay compatible with hashes created under
    4.x, which also means bytes beyond the 72nd are ignored.
    """
    long_password = 'x' * 100
    user = helpers.make_admin(password=long_password)
    assert user.verify_password(long_password) is True
    assert user.verify_password('x' * 72) is True
    assert user.verify_password('x' * 71) is False


def test_setting_new_password_invalidates_old(app):
    user = helpers.make_admin(password='spamspamspam')
    user.password = 'eggseggseggs'
    assert user.verify_password('spamspamspam') is False
    assert user.verify_password('eggseggseggs') is True


def test_authenticate_correct_credentials(app):
    user = helpers.make_admin(username='monty', password='spamspamspam')
    assert models.AdminUser.authenticate('monty', 'spamspamspam') is user


def test_authenticate_wrong_password(app):
    helpers.make_admin(username='monty', password='spamspamspam')
    assert models.AdminUser.authenticate('monty', 'wrongwrong') is None


def test_authenticate_unknown_user(app):
    helpers.make_admin(username='monty', password='spamspamspam')
    assert models.AdminUser.authenticate('brian', 'spamspamspam') is None
