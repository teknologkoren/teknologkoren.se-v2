import datetime

import flask
import flask_login

from teknologkoren_se import forms, models, util, locale
from teknologkoren_se.locale import get_string

mod = flask.Blueprint(
    'public',
    __name__,
    url_prefix='/<any(sv, en):lang_code>'
)

locale.bp_url_processors(mod)


def setup_jinja(app):
    app.jinja_env.globals['url_for_other_page'] = util.url_for_other_page
    app.jinja_env.globals['image_url'] = util.image_uploads.url
    app.jinja_env.globals['image_dest'] = lambda: (util.image_uploads.config
                                                   .base_url)


@mod.route('/', defaults={'page': 1})
@mod.route('/blogg/sida/<int:page>')
def index(page):
    posts = (
        models.Post.query
        .filter(models.Post.published < datetime.datetime.utcnow())
        .order_by(models.Post.published.desc())
    )

    config = models.Config.query.first()
    if config.flash:
        flask.flash(config.flash, config.flash_type or 'info')

    pagination = posts.paginate(page, 5)
    return flask.render_template('public/index.html',
                                 image=config.frontpage_image,
                                 pagination=pagination,
                                 page=page)


@mod.route('/konserter/', defaults={'page': 1})
@mod.route('/konserter/sida/<int:page>')
def events(page):
    events = (
        models.Event.query
        .filter(models.Event.published < datetime.datetime.utcnow())
        .order_by(models.Event.published.desc())
    )

    pagination = events.paginate(page, 5)
    return flask.render_template('public/events.html',
                                 pagination=pagination,
                                 page=page)


@mod.route('/blogg/<int:post_id>/')
@mod.route('/blogg/<int:post_id>/<slug>')
def view_post(post_id, slug=None):
    post = models.BlogPost.query.get_or_404(post_id)

    if not post.published or post.published > datetime.datetime.utcnow():
        return flask.abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != post.slug:
        return flask.redirect(
            flask.url_for(
                'public.view_post',
                post_id=post_id,
                slug=post.slug
            )
        )

    return flask.render_template('public/view_post.html', post=post)


@mod.route('/konserter/<int:event_id>/')
@mod.route('/konserter/<int:event_id>/<slug>')
def view_event(event_id, slug=None):
    event = models.Event.query.get_or_404(event_id)

    if not event.published or event.published > datetime.datetime.utcnow():
        return flask.abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != event.slug:
        return flask.redirect(
            flask.url_for(
                'public.view_event',
                event_id=event_id,
                slug=event.slug
            )
        )

    return flask.render_template('public/view_post.html', post=event)


@mod.route('/kontakt')
def contact():
    contacts = (
        models.Contact.query.
        order_by(models.Contact.weight.desc())
        .all()
    )
    ordf = models.Contact.query.filter_by(title='Ordförande').first()

    return flask.render_template('public/contact.html',
                                 contacts=contacts,
                                 ordf=ordf)


def view_page_factory(path, endpoint):
    def view_page():
        page = (
            models.Page.query
            .filter_by(path=path)
            .first_or_404()
        )

        template = 'public/page.html'
        return flask.render_template(
            template,
            page=page,
            endpoint=flask.request.endpoint
        )

    return (path, endpoint, view_page)


def init_dynamic_pages():
    pages = [('om-oss', 'about'), ('boka', 'hire'),
             ('sjung', 'apply'), ('lucia', 'lucia')]
    for endpoint, path in pages:
        view_func = view_page_factory(endpoint, path)
        mod.add_url_rule(*view_func)


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
            return flask.render_template('public/login.html', form=form)

        flask_login.login_user(user, remember=form.remember.data)
        return form.redirect('admin.index')

    return flask.render_template('public/login.html', form=form)
