import datetime

import flask

from teknologkoren_se import models

from tests.helpers import login, make_admin, make_blogpost, make_event

# The app and client pytest fixtures live in tests/conftest.py, where pytest
# picks them up automatically without imports.


def make_draft_blogpost(title_sv='Ett utkast', text_sv='Hemligt!', **kwargs):
    """A blog post with published=None, i.e. not visible to the public.

    tests/helpers.make_blogpost treats published=None as "use the
    default (an hour ago)", so drafts get their own helper.
    """
    post = models.BlogPost(
        published=None,
        title_sv=title_sv,
        text_sv=text_sv,
        **kwargs
    )
    models.db.session.add(post)
    models.db.session.commit()
    return post


def make_draft_event(title_sv='Hemlig konsert', text_sv='Hemligt!',
                     location_sv='Nya Matsalen', **kwargs):
    """An event with published=None, i.e. not visible to the public."""
    event = models.Event(
        published=None,
        title_sv=title_sv,
        text_sv=text_sv,
        start_time=(datetime.datetime.utcnow()
                    + datetime.timedelta(days=7)),
        location_sv=location_sv,
        **kwargs
    )
    models.db.session.add(event)
    models.db.session.commit()
    return event


def in_an_hour():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=1)


class TestIndex:
    def test_status(self, client):
        response = client.get('/sv/')
        assert response.status_code == 200

    def test_published_post_is_shown(self, client):
        make_blogpost(title_sv='Publicerat inlägg')

        response = client.get('/sv/')
        text = response.get_data(as_text=True)

        assert 'Publicerat inlägg' in text

    def test_published_event_is_shown(self, client):
        """The frontpage feed contains events too, not only blog posts."""
        make_event(title_sv='Vårkonsert i Nya Matsalen')

        response = client.get('/sv/')
        text = response.get_data(as_text=True)

        assert 'Vårkonsert i Nya Matsalen' in text

    def test_draft_post_is_hidden(self, client):
        make_draft_blogpost(title_sv='Opublicerat utkast')

        response = client.get('/sv/')
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Opublicerat utkast' not in text

    def test_future_post_is_hidden(self, client):
        make_blogpost(title_sv='Framtida inlägg', published=in_an_hour())

        response = client.get('/sv/')
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Framtida inlägg' not in text

    def test_pagination(self, client):
        """Six published posts: five on page 1, the oldest on page 2."""
        base = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        for i in range(6):
            make_blogpost(
                title_sv='Inlägg nummer {}'.format(i),
                published=base + datetime.timedelta(minutes=i),
            )

        page1 = client.get('/sv/').get_data(as_text=True)
        response = client.get('/sv/blogg/sida/2')
        page2 = response.get_data(as_text=True)

        assert response.status_code == 200
        # Newest five (1-5) on page 1, the oldest (0) on page 2.
        for i in range(1, 6):
            assert 'Inlägg nummer {}'.format(i) in page1
            assert 'Inlägg nummer {}'.format(i) not in page2
        assert 'Inlägg nummer 0' not in page1
        assert 'Inlägg nummer 0' in page2

    def test_pagination_past_last_page_404s(self, client):
        make_blogpost()

        response = client.get('/sv/blogg/sida/2')
        assert response.status_code == 404


class TestFrontpageFlash:
    def test_no_flash_by_default(self, client):
        response = client.get('/sv/')
        text = response.get_data(as_text=True)

        assert '<ul class="flashes">' not in text

    def test_flash_sv_shown_on_sv(self, client):
        config = models.Config.query.first()
        config.flash_sv = 'Viktig svensk banner!'
        models.db.session.commit()

        text = client.get('/sv/').get_data(as_text=True)
        assert 'Viktig svensk banner!' in text

    def test_each_language_gets_its_own_flash(self, client):
        config = models.Config.query.first()
        config.flash_sv = 'Viktig svensk banner!'
        config.flash_en = 'Important English banner!'
        models.db.session.commit()

        sv_text = client.get('/sv/').get_data(as_text=True)
        assert 'Viktig svensk banner!' in sv_text
        assert 'Important English banner!' not in sv_text

        en_text = client.get('/en/').get_data(as_text=True)
        assert 'Important English banner!' in en_text
        assert 'Viktig svensk banner!' not in en_text

    def test_flash_sv_falls_back_to_en(self, client):
        config = models.Config.query.first()
        config.flash_en = 'Important English banner!'
        models.db.session.commit()

        text = client.get('/sv/').get_data(as_text=True)
        assert 'Important English banner!' in text

    def test_flash_en_falls_back_to_sv(self, client):
        config = models.Config.query.first()
        config.flash_sv = 'Viktig svensk banner!'
        models.db.session.commit()

        text = client.get('/en/').get_data(as_text=True)
        assert 'Viktig svensk banner!' in text


class TestEvents:
    def test_status(self, client):
        response = client.get('/sv/konserter/')
        assert response.status_code == 200

    def test_published_event_is_shown(self, client):
        make_event(title_sv='Luciakonsert i Kårhuset')

        text = client.get('/sv/konserter/').get_data(as_text=True)
        assert 'Luciakonsert i Kårhuset' in text

    def test_draft_event_is_hidden(self, client):
        make_draft_event(title_sv='Hemlig spelning')

        response = client.get('/sv/konserter/')
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Hemlig spelning' not in text

    def test_future_event_is_hidden(self, client):
        make_event(title_sv='Framtida spelning', published=in_an_hour())

        text = client.get('/sv/konserter/').get_data(as_text=True)
        assert 'Framtida spelning' not in text


class TestViewPost:
    def test_correct_slug(self, client):
        post = make_blogpost(title_sv='Ett inlägg')

        response = client.get('/sv/blogg/{}/ett-inlagg'.format(post.id))
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Ett inlägg' in text

    def test_missing_slug_redirects_to_canonical(self, client):
        post = make_blogpost(title_sv='Ett inlägg')

        response = client.get('/sv/blogg/{}/'.format(post.id))

        assert response.status_code == 302
        assert response.headers['Location'].endswith(
            '/sv/blogg/{}/ett-inlagg'.format(post.id)
        )

    def test_wrong_slug_redirects_to_canonical(self, client):
        post = make_blogpost(title_sv='Ett inlägg')

        response = client.get('/sv/blogg/{}/fel-slugg'.format(post.id))

        assert response.status_code == 302
        assert response.headers['Location'].endswith(
            '/sv/blogg/{}/ett-inlagg'.format(post.id)
        )

    def test_draft_404s(self, client):
        post = make_draft_blogpost(title_sv='Ett utkast')

        response = client.get('/sv/blogg/{}/ett-utkast'.format(post.id))
        assert response.status_code == 404

    def test_future_404s(self, client):
        post = make_blogpost(title_sv='Ett inlägg', published=in_an_hour())

        response = client.get('/sv/blogg/{}/ett-inlagg'.format(post.id))
        assert response.status_code == 404

    def test_nonexistent_404s(self, client):
        response = client.get('/sv/blogg/1234/')
        assert response.status_code == 404


class TestViewEvent:
    def test_correct_slug(self, client):
        event = make_event(title_sv='En konsert')

        response = client.get('/sv/konserter/{}/en-konsert'.format(event.id))
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'En konsert' in text

    def test_missing_slug_redirects_to_canonical(self, client):
        event = make_event(title_sv='En konsert')

        response = client.get('/sv/konserter/{}/'.format(event.id))

        assert response.status_code == 302
        assert response.headers['Location'].endswith(
            '/sv/konserter/{}/en-konsert'.format(event.id)
        )

    def test_wrong_slug_redirects_to_canonical(self, client):
        event = make_event(title_sv='En konsert')

        response = client.get('/sv/konserter/{}/fel-slugg'.format(event.id))

        assert response.status_code == 302
        assert response.headers['Location'].endswith(
            '/sv/konserter/{}/en-konsert'.format(event.id)
        )

    def test_draft_404s(self, client):
        event = make_draft_event(title_sv='Hemlig konsert')

        response = client.get(
            '/sv/konserter/{}/hemlig-konsert'.format(event.id)
        )
        assert response.status_code == 404

    def test_future_404s(self, client):
        event = make_event(title_sv='En konsert', published=in_an_hour())

        response = client.get('/sv/konserter/{}/en-konsert'.format(event.id))
        assert response.status_code == 404

    def test_nonexistent_404s(self, client):
        response = client.get('/sv/konserter/1234/')
        assert response.status_code == 404


class TestContact:
    @staticmethod
    def make_contact(title, name, weight, email='x@teknologkoren.se',
                     phone=None):
        contact = models.Contact(
            title=title,
            name=name,
            email=email,
            phone=phone,
            weight=weight,
        )
        models.db.session.add(contact)
        models.db.session.commit()
        return contact

    def test_status(self, client):
        response = client.get('/sv/kontakt')
        assert response.status_code == 200

    def test_contacts_ordered_by_weight_desc(self, client):
        # Created in neither ascending nor descending weight order.
        self.make_contact('Sekreterare', 'Patsy Squire', weight=80)
        self.make_contact('Ordförande', 'King Arthur', weight=100)
        self.make_contact('Kassör', 'Sir Lancelot', weight=70)
        self.make_contact('Vice ordförande', 'Sir Bedevere', weight=90)

        text = client.get('/sv/kontakt').get_data(as_text=True)

        positions = [
            text.index('King Arthur'),
            text.index('Sir Bedevere'),
            text.index('Patsy Squire'),
            text.index('Sir Lancelot'),
        ]
        assert positions == sorted(positions)

    def test_chairperson_phone_is_formatted(self, client):
        self.make_contact('Ordförande', 'King Arthur', weight=100,
                          phone='0701234567')

        text = client.get('/sv/kontakt').get_data(as_text=True)

        assert 'King Arthur' in text
        assert '+46 70 123 45 67' in text
        assert '0701234567' not in text

    def test_chairperson_without_valid_phone_has_no_phone_paragraph(
            self, client):
        self.make_contact('Ordförande', 'King Arthur', weight=100,
                          phone='not a number')

        response = client.get('/sv/kontakt')
        assert response.status_code == 200
        text = response.get_data(as_text=True)

        assert 'King Arthur' in text
        assert 'tel:' not in text


class TestDynamicPages:
    """The static-content pages created by init_dynamic_pages().

    init_dynamic_pages() looks buggy at first glance: the list holds
    (path, endpoint) tuples but the loop unpacks them as
    `for endpoint, path in pages` and then calls
    view_page_factory(endpoint, path), whose signature is
    (path, endpoint). The two swaps cancel out, so the urls, endpoints
    and Page rows do line up: /sv/om-oss is endpoint 'public.about' and
    serves Page(path='om-oss'), etc. These tests pin down that actual
    behavior.
    """

    # (url path, endpoint, Page.path, seeded Swedish title)
    pages = [
        ('/sv/om-oss', 'public.about', 'om-oss', 'Om oss'),
        ('/sv/boka', 'public.hire', 'boka', 'Boka oss'),
        ('/sv/sjung', 'public.apply', 'sjung', 'Sjung med'),
        ('/sv/lucia', 'public.lucia', 'lucia', 'Boka luciatåg'),
    ]

    def test_urls_map_to_expected_endpoints(self, app):
        with app.test_request_context('/sv/'):
            for url, endpoint, _, _ in self.pages:
                assert flask.url_for(endpoint, lang_code='sv') == url

    def test_each_url_serves_its_own_page(self, client):
        # Give every Page row unmistakable content, then check that
        # each url renders the right row's content and nobody else's.
        for _, _, path, _ in self.pages:
            page = models.Page.query.filter_by(path=path).one()
            page.text_sv = 'Unik text för sidan {}.'.format(path)
        models.db.session.commit()

        for url, _, path, title_sv in self.pages:
            response = client.get(url)
            text = response.get_data(as_text=True)

            assert response.status_code == 200
            assert '{} | Kongl. Teknologkören'.format(title_sv) in text
            assert 'Unik text för sidan {}.'.format(path) in text
            for _, _, other_path, _ in self.pages:
                if other_path != path:
                    assert ('Unik text för sidan {}.'.format(other_path)
                            not in text)

class TestLogin:
    def test_get(self, client):
        response = client.get('/sv/login')
        assert response.status_code == 200

    def test_wrong_credentials(self, client):
        make_admin(username='monty', password='spamspamspam')

        response = client.post(
            '/sv/login',
            data={'username': 'monty', 'password': 'wrongwrong'},
        )
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Fel användarnamn eller lösenord.' in text

    def test_unknown_user(self, client):
        response = client.post(
            '/sv/login',
            data={'username': 'nobody', 'password': 'whatever'},
        )
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'Fel användarnamn eller lösenord.' in text

    def test_correct_credentials_redirect_to_admin(self, client):
        make_admin(username='monty', password='spamspamspam')

        response = login(client, 'monty', 'spamspamspam')

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/admin/')

        # And the session really is authenticated now.
        response = client.get('/admin/')
        assert response.status_code == 200

    def test_login_page_redirects_when_already_authenticated(self, client):
        make_admin()
        login(client)

        response = client.get('/sv/login')

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/admin/')

    def test_logout(self, client):
        make_admin()
        login(client)

        response = client.get('/admin/logout')
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/sv/')

        # Admin pages require login again.
        response = client.get('/admin/')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_logout_when_not_logged_in(self, client):
        response = client.get('/sv/')  # establish a lang cookie
        response = client.get('/admin/logout')

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/sv/')
