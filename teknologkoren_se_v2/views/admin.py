import flask
import flask_login
from teknologkoren_se_v2 import models, util, locale, forms
from teknologkoren_se_v2.locale import get_string

mod = flask.Blueprint(
    'admin',
    __name__,
    url_prefix='/<any(sv, en):lang_code>/admin'
)

locale.bp_url_processors(mod)

login_manager = flask_login.LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'


def setup_jinja(app):
    app.jinja_env.globals['url_for_other_page'] = util.url_for_other_page
    app.jinja_env.globals['image_url'] = util.image_uploads.url
    app.jinja_env.globals['image_dest'] = lambda: (util
                                                   .image_uploads
                                                   .config
                                                   .base_url)


@login_manager.user_loader
def load_user(user_id):
    """Tell flask-login how to get logged in user."""
    return models.User.query.get(user_id)


@mod.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()

    if flask_login.current_user.is_authenticated:
        return form.redirect('admin.index')

    if form.validate_on_submit():
        user = models.User.authenticate(form.username.data, form.password.data)

        if not user:
            flask.flash(get_string('wrong-login'), 'error')
            return flask.render_template('admin/login.html', form=form)

        flask_login.login_user(user, remember=form.remember.data)
        return form.redirect('admin.index')

    return flask.render_template('admin/login.html', form=form)


@mod.route('/')
def index():
    return "Inloggad!"
