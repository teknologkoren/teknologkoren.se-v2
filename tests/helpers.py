import datetime

from teknologkoren_se import models

# The app and client pytest fixtures live in tests/conftest.py, where pytest
# picks them up automatically without imports.


def make_admin(username='monty', password='spamspamspam'):
    """Create an admin user, commit it and return it."""
    user = models.AdminUser(username=username, password=password)
    models.db.session.add(user)
    models.db.session.commit()
    return user


def login(client, username='monty', password='spamspamspam'):
    """Log in through the login view, like a browser would."""
    return client.post(
        '/sv/login',
        data={'username': username, 'password': password},
    )


def make_blogpost(published=None, title_sv='Ett inlägg', text_sv='Hej!',
                  **kwargs):
    """Create a blog post, commit it and return it.

    `published` defaults to an hour ago, i.e. the post is visible.
    """
    if published is None:
        published = (datetime.datetime.utcnow()
                     - datetime.timedelta(hours=1))
    post = models.BlogPost(
        published=published,
        title_sv=title_sv,
        text_sv=text_sv,
        **kwargs
    )
    models.db.session.add(post)
    models.db.session.commit()
    return post


def make_event(published=None, title_sv='En konsert', text_sv='Kom!',
               start_time=None, location_sv='Nya Matsalen', **kwargs):
    """Create an event, commit it and return it.

    `published` defaults to an hour ago, `start_time` to a week from now.
    """
    if published is None:
        published = (datetime.datetime.utcnow()
                     - datetime.timedelta(hours=1))
    if start_time is None:
        start_time = (datetime.datetime.utcnow()
                      + datetime.timedelta(days=7))
    event = models.Event(
        published=published,
        title_sv=title_sv,
        text_sv=text_sv,
        start_time=start_time,
        location_sv=location_sv,
        **kwargs
    )
    models.db.session.add(event)
    models.db.session.commit()
    return event
