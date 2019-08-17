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
    from teknologkoren_se_v2 import models

    with open('lorem.txt') as lorem:
        def 


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

    posts = [
        models.Post(
            title="A test post",
        )
    ]



def init_db(app):
    from teknologkoren_se_v2 import models
    models.db.create_all(app=app)


def setup_flask_uploads(app):
    import flask_uploads
    from teknologkoren_se_v2 import util

    flask_uploads.configure_uploads(app, util.image_uploads)

    app.jinja_env.globals['url_for_image'] = util.url_for_image


def setup_locale(app):
    from teknologkoren_se_v2 import locale
    app.jinja_env.globals['locale'] = locale
    app.jinja_env.globals['_'] = locale.get_string
    app.jinja_env.globals['url_for_lang'] = locale.url_for_lang

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
