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


@flask_login.login_required
@mod.route('/')
def index():
    pages = models.Page.query.all()
    posts = models.BlogPost.query.all()
    events = models.Event.query.all()
    return flask.render_template(
        'admin/index.html',
        pages=pages,
        posts=posts,
        events=events
    )


@flask_login.login_required
@mod.route('/post/new', methods=['GET', 'POST'])
@mod.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id=None):
    if post_id:
        post = models.Post.query.get_or_404(post_id)
    else:
        post = None

    form = forms.EditPostForm(obj=post)

    if form.validate_on_submit():
        if not post:
            post = models.Post()

        post.published = forms.none_if_space(form.published.data)

        post.title_sv = form.title_sv.data
        post.title_en = forms.none_if_space(form.title_en.data)

        post.text_sv = form.text_sv.data
        post.text_en = forms.none_if_space(form.text_en.data)

        if form.image.data:
            filename = util.image_uploads.save(form.image.data)
            image = models.Image(filename=filename)
            models.db.session.add(image)

            image.portrait = form.portrait.data
            post.image = image

        elif post.image:
            post.image.portrait = form.portrait.data

        if not post_id:
            models.db.session.add(post)

        models.db.session.commit()

        if post_id:
            flask.flash("Uppdaterad!", 'success')
        else:
            flask.flash("Inlägg skapat!", 'success')

        flask.redirect(flask.url_for('admin.post', post_id=post.id))

    else:
        forms.flash_errors(form)

    if post.image:
        form.portrait.data = post.image.portrait

    return flask.render_template('admin/post.html', post=post, form=form)


@flask_login.login_required
@mod.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event(event_id):
    event = models.Event.query.get(event_id)

    form = forms.EditEventForm(obj=event)

    if form.validate_on_submit():
        event.published = forms.none_if_space(form.published.data)

        event.title_sv = form.title_sv.data
        event.title_en = forms.none_if_space(form.title_en.data)

        event.text_sv = form.text_sv.data
        event.text_en = forms.none_if_space(form.text_en.data)

        event.start_time = form.start_time.data

        event.time_text_sv = forms.none_if_space(form.time_text_sv.data)
        event.time_text_en = forms.none_if_space(form.time_text_en.data)

        event.location_sv = form.location_sv.data
        event.location_en = forms.none_if_space(form.location_en.data)

        event.location_link = forms.none_if_space(form.location_link.data)

        if form.image.data:
            filename = util.image_uploads.save(form.image.data)
            image = models.Image(filename=filename)
            models.db.session.add(image)

            image.portrait = form.portrait.data
            event.image = image

        elif event.image:
            event.image.portrait = form.portrait.data

        models.db.session.commit()

        flask.flash("Uppdaterad!", 'success')

        flask.redirect(flask.url_for('admin.event', event_id=event.id))

    else:
        forms.flash_errors(form)

    if event.image:
        form.portrait.data = event.image.portrait

    return flask.render_template('admin/event.html', event=event, form=form)
