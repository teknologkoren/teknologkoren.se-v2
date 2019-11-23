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
    return models.AdminUser.query.get(user_id)


@mod.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()

    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('admin.index'))

    if form.validate_on_submit():
        user = models.AdminUser.authenticate(
            form.username.data,
            form.password.data
        )

        if not user:
            flask.flash(get_string('wrong-login'), 'error')
            return flask.render_template('admin/login.html', form=form)

        flask_login.login_user(user, remember=form.remember.data)
        return form.redirect('admin.index')

    return flask.render_template('admin/login.html', form=form)


@mod.route('/logout')
def logout():
    if flask_login.current_user.is_authenticated:
        flask_login.logout_user()

    return flask.redirect(flask.url_for('public.index'))


@mod.route('/')
@flask_login.login_required
def index():
    pages = models.Page.query.all()
    posts = models.Post.query.filter_by(is_event=False)
    events = models.Post.query.filter_by(is_event=True)
    return flask.render_template(
        'admin/index.html', pages=pages, posts=posts, events=events
    )


@mod.route('/post/<int:post_id>')
@mod.route('/post/<int:post_id>/<int:content_id>')
def post(post_id, content_id=None):
    post = models.Post.query.get(post_id)

    if content_id:
        content = models.PostContent.query.get(content_id)
        if content.post_id != post_id:
            flask.abort(404)
    else:
        content = post.content

    form = forms.EditPostForm(obj=content)
    form.published.data = post.published

    return flask.render_template(
        'admin/post.html', post=post, content=content, form=form
    )


@mod.route('/event/<int:post_id>')
@mod.route('/event/<int:post_id>/<int:content_id>')
def event(post_id, content_id=None):
    event = models.Post.query.get(post_id)

    if content_id:
        content = models.PostContent.query.get(content_id)
        if content.post_id != post_id:
            flask.abort(404)
    else:
        content = event.content

    form = forms.EditEventForm(obj=content)
    form.published.data = event.published

    return flask.render_template(
        'admin/event.html', event=event, content=content, form=form
    )
