import base64
import datetime
import io
import os

import pytest

from teknologkoren_se import models, util
from tests import helpers

# The app and client pytest fixtures live in tests/conftest.py.

# A real (valid) 1x1 px PNG, for upload tests.
PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ'
    'AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


def login_admin(client):
    """Create an admin user, log in with it and return it."""
    user = helpers.make_admin()
    helpers.login(client)
    return user


def refresh():
    """Drop cached attribute state so asserts read what a view committed."""
    models.db.session.expire_all()


# Login protection

@pytest.mark.parametrize('path', [
    '/admin/',
    '/admin/frontpage',
    '/admin/contacts',
    '/admin/post/new',
    '/admin/event/new',
    '/admin/users',
    '/admin/page/1',
])
def test_admin_views_redirect_anonymous_to_login(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


@pytest.mark.parametrize('path', [
    '/admin/files/',
    '/admin/files/file/',
    '/admin/files/image/',
])
def test_files_views_are_not_login_protected(client, path):
    # KNOWN BUG (teknologkoren_se/views/admin.py:457, :464, :500): the
    # files(), file() and image() views are the only admin views without
    # @flask_login.login_required, so anonymous visitors can list all
    # uploads and upload/replace files and images. These tests document
    # the current (unprotected) behavior; when the views gain login
    # protection they should be moved into the parametrize list above.
    response = client.get(path)
    assert response.status_code == 200


def test_file_upload_is_not_login_protected(client):
    # KNOWN BUG, see test_files_views_are_not_login_protected: this
    # upload succeeds without any login.
    response = client.post('/admin/files/file/', data={
        'file': (io.BytesIO(b'anonymous was here'), 'anon-upload.txt'),
    })
    assert response.status_code == 302
    assert models.File.query.filter_by(type='file').count() == 1


# Admin index

def test_admin_index_lists_posts_events_and_pages(client):
    login_admin(client)
    helpers.make_blogpost(title_sv='Julkonsert i Storkyrkan')
    helpers.make_event(title_sv='Vårkonsert i Stadshuset')

    response = client.get('/admin/')
    assert response.status_code == 200

    text = response.get_data(as_text=True)
    assert 'Julkonsert i Storkyrkan' in text
    assert 'Vårkonsert i Stadshuset' in text
    # Pages are listed by path.
    for page in models.Page.query.all():
        assert page.path in text
        assert f'/admin/page/{page.id}' in text


# Blog posts

def test_create_post(client):
    login_admin(client)

    response = client.post('/admin/post/new', data={
        'title_sv': 'Nytt inlägg',
        'text_sv': 'Hej hej!',
        'choose_image': '-1',
        'published': '2020-01-01T12:00',
    })
    assert response.status_code == 302

    post = models.BlogPost.query.filter_by(title_sv='Nytt inlägg').one()
    assert response.headers['Location'].endswith(f'/admin/post/{post.id}')
    assert post.text_sv == 'Hej hej!'
    assert post.slug_sv == 'nytt-inlagg'
    assert post.image_id is None
    # The posted time is interpreted as CET (UTC+1 in January) and
    # stored as UTC.
    assert post.published == datetime.datetime(2020, 1, 1, 11, 0)


def test_create_post_without_published_is_unpublished(client):
    login_admin(client)

    response = client.post('/admin/post/new', data={
        'title_sv': 'Utkast',
        'text_sv': 'Hemligt än så länge.',
        'choose_image': '-1',
        'published': '',
    })
    assert response.status_code == 302

    post = models.BlogPost.query.filter_by(title_sv='Utkast').one()
    assert post.published is None


def test_edit_post(client):
    login_admin(client)
    post = helpers.make_blogpost(title_sv='Gammal titel')

    response = client.post(f'/admin/post/{post.id}', data={
        'title_sv': 'Ny titel',
        'title_en': 'New title',
        'text_sv': 'Ny text.',
        'choose_image': '-1',
        # July: CEST is UTC+2.
        'published': '2021-07-01T14:00',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith(f'/admin/post/{post.id}')

    refresh()
    assert post.title_sv == 'Ny titel'
    assert post.title_en == 'New title'
    assert post.slug_sv == 'ny-titel'
    assert post.text_sv == 'Ny text.'
    assert post.published == datetime.datetime(2021, 7, 1, 12, 0)


def test_delete_post(client):
    login_admin(client)
    post = helpers.make_blogpost()
    post_id = post.id

    response = client.get(f'/admin/post/{post_id}/remove')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/')

    refresh()
    assert models.BlogPost.query.filter_by(id=post_id).first() is None


# Events

def test_create_event(client):
    login_admin(client)

    response = client.post('/admin/event/new', data={
        'title_sv': 'Sommarkonsert',
        'text_sv': 'Välkomna!',
        'choose_image': '-1',
        'published': '2020-06-01T12:00',
        'start_time': '2020-06-13T18:00',
        'location_sv': 'Nya Matsalen',
        'location_link': 'https://example.com/karta',
    })
    assert response.status_code == 302

    event = models.Event.query.filter_by(title_sv='Sommarkonsert').one()
    assert response.headers['Location'].endswith(f'/admin/event/{event.id}')
    assert event.location_sv == 'Nya Matsalen'
    assert event.location_link == 'https://example.com/karta'
    # June: CEST is UTC+2, both timestamps are converted to UTC.
    assert event.published == datetime.datetime(2020, 6, 1, 10, 0)
    assert event.start_time == datetime.datetime(2020, 6, 13, 16, 0)


def test_create_event_requires_start_time(client):
    login_admin(client)

    response = client.post('/admin/event/new', data={
        'title_sv': 'Sommarkonsert',
        'text_sv': 'Välkomna!',
        'choose_image': '-1',
        'location_sv': 'Nya Matsalen',
    })
    # Validation fails, the form is re-rendered.
    assert response.status_code == 200
    assert models.Event.query.count() == 0


def test_edit_event(client):
    login_admin(client)
    event = helpers.make_event(title_sv='Höstkonsert')

    response = client.post(f'/admin/event/{event.id}', data={
        'title_sv': 'Höstkonsert (flyttad)',
        'text_sv': 'Ny lokal!',
        'choose_image': '-1',
        'published': '2021-01-10T09:00',
        'start_time': '2021-02-01T19:30',
        'location_sv': 'Musikaliska',
        'time_text_sv': 'Insläpp 19:00',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith(f'/admin/event/{event.id}')

    refresh()
    assert event.title_sv == 'Höstkonsert (flyttad)'
    assert event.location_sv == 'Musikaliska'
    assert event.time_text_sv == 'Insläpp 19:00'
    # January: CET is UTC+1.
    assert event.published == datetime.datetime(2021, 1, 10, 8, 0)
    assert event.start_time == datetime.datetime(2021, 2, 1, 18, 30)


def test_delete_event(client):
    login_admin(client)
    event = helpers.make_event()
    event_id = event.id

    response = client.get(f'/admin/event/{event_id}/remove')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/')

    refresh()
    assert models.Event.query.filter_by(id=event_id).first() is None


# Pages

def test_edit_page(client):
    login_admin(client)
    page = models.Page.query.filter_by(path='om-oss').one()

    response = client.post(f'/admin/page/{page.id}', data={
        'text_sv': 'Vi är en kör.',
        'text_en': 'We are a choir.',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith(f'/admin/page/{page.id}')

    refresh()
    assert page.text_sv == 'Vi är en kör.'
    assert page.text_en == 'We are a choir.'


def test_edit_page_requires_both_texts(client):
    login_admin(client)
    page = models.Page.query.filter_by(path='om-oss').one()

    response = client.post(f'/admin/page/{page.id}', data={
        'text_sv': 'Bara svenska.',
    })
    assert response.status_code == 200

    refresh()
    # init_db seeds pages with empty texts, so '' means "not updated".
    assert page.text_sv == ''
    assert page.text_sv != 'Bara svenska.'


# Frontpage

def test_frontpage_form_sets_flash(client):
    login_admin(client)

    response = client.post('/admin/frontpage', data={
        'flash_sv': 'Konsert på lördag!',
        'flash_en': 'Concert on Saturday!',
        'flash_type': 'warning',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/frontpage')

    refresh()
    config = models.Config.query.one()
    assert config.flash_sv == 'Konsert på lördag!'
    assert config.flash_en == 'Concert on Saturday!'
    assert config.flash_type == 'warning'


def test_frontpage_form_space_only_flash_becomes_none(client):
    login_admin(client)

    response = client.post('/admin/frontpage', data={
        'flash_sv': ' ',
        'flash_en': '   ',
        'flash_type': 'info',
    })
    assert response.status_code == 302

    refresh()
    config = models.Config.query.one()
    # none_if_space() turns whitespace-only strings into None.
    assert config.flash_sv is None
    assert config.flash_en is None
    assert config.flash_type == 'info'


def test_frontpage_form_uploads_frontpage_image(client):
    login_admin(client)

    response = client.post('/admin/frontpage', data={
        'flash_sv': '',
        'flash_en': '',
        'flash_type': 'info',
        'frontpage_image-image': (io.BytesIO(PNG_BYTES),
                                  'admin-frontpage-test.png'),
    })
    assert response.status_code == 302

    refresh()
    config = models.Config.query.one()
    assert config.frontpage_image is not None
    assert config.frontpage_image.filename.endswith('.png')
    assert config.frontpage_image.portrait is False
    assert os.path.isfile(
        util.image_uploads.path(config.frontpage_image.filename)
    )


# Users

def test_users_add_new_user(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        'new-user-username': 'brian',
        'new-user-password': 'notthemessiah',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/users')

    refresh()
    new_user = models.AdminUser.query.filter_by(username='brian').one()
    assert new_user.verify_password('notthemessiah')


def test_users_reject_duplicate_username(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        'new-user-username': 'monty',
        'new-user-password': 'notthemessiah',
    })
    assert response.status_code == 200
    assert 'upptaget' in response.get_data(as_text=True)

    refresh()
    assert models.AdminUser.query.count() == 1


def test_users_reject_new_user_without_password(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        'new-user-username': 'brian',
    })
    assert response.status_code == 200
    assert 'Ange ett lösenord' in response.get_data(as_text=True)

    refresh()
    assert models.AdminUser.query.count() == 1


def test_users_reject_too_short_password(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        'new-user-username': 'brian',
        'new-user-password': 'short',  # Length(8) validator should reject
    })
    assert response.status_code == 200

    refresh()
    assert models.AdminUser.query.count() == 1


def test_users_cannot_delete_own_user(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        f'user-{admin.id}-delete': 'y',
        # A browser always submits the (empty) new-user text input. The
        # view crashes with AttributeError if the key is missing
        # entirely (admin.py:398 calls .data.strip() on None), but that
        # is not reachable from the rendered form.
        'new-user-username': '',
    })
    assert response.status_code == 200
    assert 'inloggad med' in response.get_data(as_text=True)

    refresh()
    assert models.AdminUser.query.filter_by(username='monty').count() == 1


def test_users_can_delete_other_user(client):
    admin = login_admin(client)
    other = helpers.make_admin(username='brian', password='notthemessiah')

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        f'user-{other.id}-username': 'brian',
        f'user-{other.id}-delete': 'y',
        'new-user-username': '',
    })
    assert response.status_code == 302

    refresh()
    assert models.AdminUser.query.filter_by(username='brian').count() == 0
    assert models.AdminUser.query.filter_by(username='monty').count() == 1


def test_users_change_password(client):
    admin = login_admin(client)

    response = client.post('/admin/users', data={
        f'user-{admin.id}-username': 'monty',
        f'user-{admin.id}-password': 'flyingcircus',
        'new-user-username': '',
    })
    assert response.status_code == 302

    refresh()
    assert admin.verify_password('flyingcircus')
    assert not admin.verify_password('spamspamspam')


def test_users_post_without_new_user_field_crashes(client):
    # KNOWN BUG (teknologkoren_se/views/admin.py:398): the users view
    # calls sub_form.username.data.strip() on the new-user subform, but
    # if a hand-crafted POST omits the new-user-username key the field's
    # data is None and the view raises AttributeError (500 in
    # production). Browsers always submit the empty text input, so the
    # rendered form cannot trigger this. This test documents the current
    # behavior; if the view is fixed, assert a redirect instead.
    admin = login_admin(client)

    with pytest.raises(AttributeError):
        client.post('/admin/users', data={
            f'user-{admin.id}-username': 'monty',
        })


# Contacts

def test_contacts_add_new_contact(client):
    login_admin(client)

    response = client.post('/admin/contacts', data={
        'new-contact-title': 'Sekreterare',
        'new-contact-name': 'Hedda Hopper',
        'new-contact-email': 'hedda@teknologkoren.se',
        'new-contact-phone': '0711234567',
        'new-contact-weight': '50',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/contacts')

    contact = models.Contact.query.filter_by(name='Hedda Hopper').one()
    assert contact.title == 'Sekreterare'
    assert contact.email == 'hedda@teknologkoren.se'
    assert contact.phone == '0711234567'
    assert contact.weight == 50


def test_contacts_empty_new_contact_subform_is_ignored(client):
    login_admin(client)

    response = client.post('/admin/contacts', data={})
    assert response.status_code == 302
    assert models.Contact.query.count() == 0


def test_contacts_edit_existing_contact(client):
    login_admin(client)
    contact = helpers.make_contact()

    response = client.post('/admin/contacts', data={
        f'contact-{contact.id}-title': 'Vice ordförande',
        f'contact-{contact.id}-name': 'Terry Gilliam',
        f'contact-{contact.id}-email': 'vice@teknologkoren.se',
        f'contact-{contact.id}-phone': '',
        f'contact-{contact.id}-weight': '90',
    })
    assert response.status_code == 302

    refresh()
    assert contact.title == 'Vice ordförande'
    assert contact.name == 'Terry Gilliam'
    assert contact.email == 'vice@teknologkoren.se'
    assert contact.phone == ''
    assert contact.weight == 90


def test_contacts_delete_contact(client):
    login_admin(client)
    contact = helpers.make_contact()
    contact_id = contact.id

    response = client.post('/admin/contacts', data={
        f'contact-{contact_id}-title': 'Ordförande',
        f'contact-{contact_id}-name': 'Monty Python',
        f'contact-{contact_id}-email': 'ordf@teknologkoren.se',
        f'contact-{contact_id}-phone': '0701234567',
        f'contact-{contact_id}-weight': '100',
        f'contact-{contact_id}-delete': 'y',
    })
    assert response.status_code == 302

    refresh()
    assert models.Contact.query.filter_by(id=contact_id).first() is None


# Files and images
# (These views are missing login protection, see
# test_files_views_are_not_login_protected. The upload flow itself is
# tested logged in, as it is meant to be used.)

def test_upload_file(client):
    login_admin(client)

    response = client.post('/admin/files/file/', data={
        'file': (io.BytesIO(b'hello world'), 'admin-test-notes.txt'),
    })
    assert response.status_code == 302

    file = models.File.query.filter_by(type='file').one()
    assert response.headers['Location'].endswith(
        f'/admin/files/file/{file.id}'
    )
    assert file.filename.endswith('.txt')
    assert os.path.isfile(util.file_uploads.path(file.filename))


def test_upload_file_without_file_is_rejected(client):
    login_admin(client)

    response = client.post('/admin/files/file/', data={})
    assert response.status_code == 200
    assert models.File.query.filter_by(type='file').count() == 0


def test_upload_image(client):
    login_admin(client)

    response = client.post('/admin/files/image/', data={
        'image': (io.BytesIO(PNG_BYTES), 'admin-test-image.png'),
        'portrait': 'y',
    })
    assert response.status_code == 302

    image = models.Image.query.one()
    assert response.headers['Location'].endswith(
        f'/admin/files/image/{image.id}'
    )
    assert image.filename.endswith('.png')
    assert image.portrait is True
    assert os.path.isfile(util.image_uploads.path(image.filename))


def test_upload_image_rejects_non_image_extension(client):
    login_admin(client)

    response = client.post('/admin/files/image/', data={
        'image': (io.BytesIO(b'not an image'), 'admin-test-evil.exe'),
    })
    assert response.status_code == 200
    assert models.Image.query.count() == 0
