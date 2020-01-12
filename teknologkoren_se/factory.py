import click
import flask


def create_app(config=None, instance_config=None):
    app = flask.Flask(__name__, instance_relative_config=True)
    # Load default config
    app.config.from_object('config')

    if instance_config:
        # Load instance config
        app.config.from_pyfile(instance_config)

    # Load config dict
    app.config.update(config or {})

    register_blueprints(app)
    register_cli(app)

    from teknologkoren_se import models, views, util

    models.db.init_app(app)
    with app.app_context():
        init_db(app)

    util.bcrypt.init_app(app)

    views.admin.login_manager.init_app(app)
    views.public.setup_jinja(app)

    setup_flask_uploads(app)
    setup_locale(app)

    from teknologkoren_se.lib import cache_bust
    cache_bust.init_cache_busting(app)

    if app.debug:
        setup_debug_mode(app)

    return app


def register_blueprints(app):
    from teknologkoren_se.views import public, admin
    public.init_dynamic_pages()
    app.register_blueprint(public.mod)
    app.register_blueprint(admin.mod)


def register_cli(app):
    @app.cli.command('initdb')
    def initdb_command():
        init_db(app)

    @app.cli.command('dropdb')
    def dropdb_command():
        from teknologkoren_se import models
        if click.confirm("You are about to DROP *ALL* tables, are you sure "
                         "you want to do this?", abort=True):
            models.db.drop_all()

    @app.cli.command('populatetestdb')
    def populatetestdb_command():
        populate_testdb()

    @app.cli.command('createadmin')
    def createadmin_command():
        from teknologkoren_se import models
        print("Creating a new admin user...")
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True)
        user = models.AdminUser(
            username=username,
            password=password,
        )

        models.db.session.add(user)
        models.db.session.commit()


def populate_testdb():
    import datetime
    import random
    from teknologkoren_se import models

    contacts = [
        models.Contact(
            title="Ordförande",
            name="King Arthur",
            email="ordf@teknologkoren.se",
            phone="0711098765",
            weight="100"
        ),
        models.Contact(
            title="Vice ordförande",
            name="Sir Bedevere the Wise",
            email="vice@teknologkoren.se",
            weight="90"
        ),
        models.Contact(
            title="Sekreterare",
            name="Patsy Squire",
            email="sekr@teknologkoren.se",
            weight="80"
        ),
        models.Contact(
            title="Kassör",
            name="Sir Lancelot the Brave",
            email="pengar@teknologkoren.se",
            weight="70"
        ),
        models.Contact(
            title="Qlubbmästare",
            name="Sir Galahad the Pure",
            email="qm@teknologkoren.se",
            weight="60"
        ),
        models.Contact(
            title="Notfisqual",
            name="Sir Robin the Not-Quite-So-Brave-as-Sir-Lancelot",
            email="ordf@teknologkoren.se",
            weight="50"
        ),
        models.Contact(
            title="Proletär",
            name="Sir Not-Appearing-on-this-Page",
            email="pr@teknologkoren.se",
            weight="40"
        )
    ]

    models.db.session.add_all(contacts)

    with open('teknologkoren_se/lorem_lines.txt') as f:
        lorem_lines = [l.strip() for l in f.readlines()]

    with open('teknologkoren_se/lorem_paragraphs.txt') as f:
        lorem_paragraphs = [l.strip() for l in f.readlines()]

    def lipsum_line():
        return random.choice(lorem_lines)

    def lipsum_paragraphs(n):
        return '\n\n'.join(random.sample(lorem_paragraphs, n))

    pages = [
        {
            'path': 'about',
            'heading-sv': "Om oss",
            'heading-en': "About us"
        },
        {
            'path': 'hire',
            'heading-sv': "Boka oss",
            'heading-en': "Hire us"
        },
        {
            'path': 'apply',
            'heading-sv': "Sjung med oss",
            'heading-en': "Apply"
        },
        {
            'path': 'lucia',
            'heading-sv': "Boka luciatåg",
            'heading-en': "Book a Lucia procession"
        }
    ]
    for page in pages:
        text_sv = "# {}\n\n{}".format(
            page['heading-sv'],
            lipsum_paragraphs(4)
        )
        text_en = "# {}\n\n{}".format(
            page['heading-en'],
            lipsum_paragraphs(4)
        )
        page_obj = models.Page.query.filter_by(path=page['path']).first()
        page_obj.text_sv=text_sv
        page_obj.text_en=text_en

    models.db.session.commit()

    posts = []
    for i in range(5):
        published = (
            datetime.datetime.utcnow()
            - datetime.timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )

        text_len = random.choice([1]*2 + [2]*3 + [3])

        posts.append(
            models.BlogPost(
                published=published,
                title_sv=lipsum_line().replace('.', ''),
                title_en=lipsum_line().replace('.', ''),
                text_sv=lipsum_paragraphs(text_len),
                text_en=lipsum_paragraphs(text_len),
            )
        )

    events = []
    for i in range(6):
        published = (
            datetime.datetime.utcnow()
            - datetime.timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )

        start_time = (
            published
            + datetime.timedelta(
                days=random.randint(10, 120),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )

        text_len = random.choice([1]*2 + [2]*3 + [3])

        location = lipsum_line().replace('.', '')

        events.append(
            models.Event(
                published=published,
                title_sv=lipsum_line().replace('.', ''),
                title_en=lipsum_line().replace('.', ''),
                text_sv=lipsum_paragraphs(text_len),
                text_en=lipsum_paragraphs(text_len),
                start_time=start_time,
                location_sv=location,
                location_en=location,
                location_link=(
                    "https://{}.dev/".format(
                        lipsum_line()
                        .replace(' ', '')
                        .replace(',', '.')
                        .replace('.', '')
                        .lower()
                    )
                )
            )
        )

    models.db.session.add_all(posts)
    models.db.session.add_all(events)
    models.db.session.commit()


def init_db(app):
    from teknologkoren_se import models
    models.db.create_all(app=app)

    pages = [
        ('om-oss', 'Om oss', 'About us'),
        ('boka', 'Boka oss', 'Hire us'),
        ('sjung', 'Sjung med', 'Apply'),
        ('lucia', 'Boka luciatåg', 'Boka luciatåg')
    ]
    for path, title_sv, title_en in pages:
        page = (
            models.Page.query
            .filter_by(path=path)
            .first()
        )

        if not page:
            page = models.Page(
                path=path,
                text_sv='',
                text_en='',
                title_sv=title_sv,
                title_en=title_en,
            )
            models.db.session.add(page)
            models.db.session.commit()

    if not models.Config.query.first():
        config = models.Config()
        models.db.session.add(config)
        models.db.session.commit()


def setup_flask_uploads(app):
    import flask_uploads
    from teknologkoren_se import util

    flask_uploads.configure_uploads(app, util.image_uploads)

    app.jinja_env.globals['url_for_image'] = util.url_for_image


def setup_locale(app):
    from babel.dates import (format_date, format_datetime, format_time,
                             get_timezone)
    from teknologkoren_se import locale
    app.jinja_env.globals['locale'] = locale
    app.jinja_env.globals['_'] = locale.get_string
    app.jinja_env.globals['url_for_lang'] = locale.url_for_lang

    cet = get_timezone('Europe/Stockholm')

    # locale.get_locale() requires an application context, we either
    # have to run get_locale() in the templates, or use lambdas here.
    app.jinja_env.globals['format_date'] = (
        lambda d, f: format_date(
            d, f,
            locale=locale.get_locale()
        )
    )
    app.jinja_env.globals['format_datetime'] = (
        lambda d, f: format_datetime(
            d, f,
            tzinfo=cet,
            locale=locale.get_locale()
        )
    )
    app.jinja_env.globals['format_time'] = (
        lambda d, f: format_time(
            d, f,
            tzinfo=cet,
            locale=locale.get_locale()
        )
    )

    app.before_request(locale.fix_missing_lang_code)


def setup_debug_mode(app):
    def catch_image_resize(image_size, image):
        """Redirect requests to resized images.

        Flask's built-in server does not understand the image resize
        path argument that nginx uses. This redirects those urls to the
        original images.
        """
        if flask.request.endpoint == 'image_resize':
            non_resized_url = '/static/images/{}'
        elif flask.request.endpoint == 'upload_resize':
            non_resized_url = '/static/uploads/images/{}'
        else:
            # Why are we in this function?
            flask.abort(500)

        non_resized_url = non_resized_url.format(image)

        return flask.redirect(non_resized_url)

    # If in debug mode, add rule for resized image paths to go through
    # the redirection function.
    app.add_url_rule('/static/images/<image_size>/<image>',
                     endpoint='image_resize',
                     view_func=catch_image_resize)

    app.add_url_rule('/static/uploads/images/<image_size>/<image>',
                     endpoint='upload_resize',
                     view_func=catch_image_resize)
