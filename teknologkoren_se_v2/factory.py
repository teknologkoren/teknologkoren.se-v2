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

    from teknologkoren_se_v2 import models, views, util

    models.db.init_app(app)
    init_db(app)

    util.bcrypt.init_app(app)

    #views.auth.login_manager.init_app(app)
    views.public.setup_jinja(app)

    setup_flask_uploads(app)
    setup_locale(app)

    if app.debug:
        setup_debug_mode(app)

    return app


def register_blueprints(app):
    from teknologkoren_se_v2.views import public#, admin
    app.register_blueprint(public.mod)
    #app.register_blueprint(admin.mod)


def register_cli(app):
    @app.cli.command('initdb')
    def initdb_command():
        init_db(app)

    @app.cli.command('dropdb')
    def dropdb_command():
        from teknologkoren_se_v2 import models
        if click.confirm("You are about to DROP *ALL* tables, are you sure "
                         "you want to do this?", abort=True):
            models.db.drop_all()

    @app.cli.command('populatetestdb')
    def populatetestdb_command():
        populate_testdb()


def populate_testdb():
    import datetime
    import random
    from teknologkoren_se_v2 import models

    contacts = [
        models.Contact(
            title="Ordförande",
            first_name="King",
            last_name="Arthur",
            email="ordf@teknologkoren.se",
            phone="0711098765",
            weight="100"
        ),
        models.Contact(
            title="Vice ordförande",
            first_name="Sir Bedevere",
            last_name="the Wise",
            email="vice@teknologkoren.se",
            weight="90"
        ),
        models.Contact(
            title="Sekreterare",
            first_name="Patsy",
            last_name="Squire",
            email="sekr@teknologkoren.se",
            weight="80"
        ),
        models.Contact(
            title="Kassör",
            first_name="Sir Lancelot",
            last_name="the Brave",
            email="pengar@teknologkoren.se",
            weight="70"
        ),
        models.Contact(
            title="Qlubbmästare",
            first_name="Sir Galahad",
            last_name="the Pure",
            email="qm@teknologkoren.se",
            weight="60"
        ),
        models.Contact(
            title="Notfisqual",
            first_name="Sir Robin",
            last_name="the Not-Quite-So-Brave-as-Sir-Lancelot",
            email="ordf@teknologkoren.se",
            weight="50"
        ),
        models.Contact(
            title="Proletär",
            first_name="Sir",
            last_name="Not-Appearing-on-this-Page",
            email="pr@teknologkoren.se",
            weight="40"
        )
    ]

    for contact in contacts:
        models.db.session.add(contact)

    with open('teknologkoren_se_v2/lorem_lines.txt') as f:
        lorem_lines = [l.strip() for l in f.readlines()]

    with open('teknologkoren_se_v2/lorem_paragraphs.txt') as f:
        lorem_paragraphs = [l.strip() for l in f.readlines()]

    def lipsum_line():
        return random.choice(lorem_lines)

    def lipsum_paragraphs(n):
        return '\n\n'.join(random.sample(lorem_paragraphs, n))

    post_contents = []
    for i in range(5):
        text_len = random.choice([1]*2 + [2]*3 + [3])
        timestamp = (
            datetime.datetime.utcnow()
            - datetime.timedelta(days=random.randint(-30, 0))
        )
        post_contents.append(
            models.PostContent(
                title_sv=lipsum_line().replace('.', ''),
                title_en=lipsum_line().replace('.', ''),
                text_sv=lipsum_paragraphs(text_len),
                text_en=lipsum_paragraphs(text_len),
                timestamp=timestamp
            )
        )

    event_contents = []
    for i in range(6):
        timestamp = (
            datetime.datetime.utcnow()
            - datetime.timedelta(days=random.randint(-30, 0))
        )

        if 6 - i > 2:
            start_days = random.randint(-120, -1)
        else:
            start_days = random.randint(1, 90)

        start_time = timestamp + datetime.timedelta(days=start_days)

        text_len = random.choice([1]*2 + [2]*3 + [3])

        location = lipsum_line().replace('.', '')

        event_contents.append(
            models.EventContent(
                title_sv=lipsum_line().replace('.', ''),
                title_en=lipsum_line().replace('.', ''),
                text_sv=lipsum_paragraphs(text_len),
                text_en=lipsum_paragraphs(text_len),
                timestamp=timestamp,
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

    for post_content in post_contents:
        post = models.Post(published=post_content.timestamp, is_event=False)
        models.db.session.add(post)
        models.db.session.commit()

        post_content.post_id = post.id
        models.db.session.add(post_content)
        models.db.session.commit()

    for event_content in event_contents:
        post = models.Post(published=post_content.timestamp, is_event=True)
        models.db.session.add(post)
        models.db.session.commit()

        event_content.post_id = post.id
        models.db.session.add(event_content)
        models.db.session.commit()

    models.db.session.commit()


def init_db(app):
    from teknologkoren_se_v2 import models
    models.db.create_all(app=app)


def setup_flask_uploads(app):
    import flask_uploads
    from teknologkoren_se_v2 import util

    flask_uploads.configure_uploads(app, util.image_uploads)

    app.jinja_env.globals['url_for_image'] = util.url_for_image


def setup_locale(app):
    from babel.dates import format_date, format_datetime, format_time
    from teknologkoren_se_v2 import locale
    app.jinja_env.globals['locale'] = locale
    app.jinja_env.globals['_'] = locale.get_string
    app.jinja_env.globals['url_for_lang'] = locale.url_for_lang
    app.jinja_env.globals['format_date'] = format_date
    app.jinja_env.globals['format_datetime'] = format_datetime
    app.jinja_env.globals['format_time'] = format_time

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
