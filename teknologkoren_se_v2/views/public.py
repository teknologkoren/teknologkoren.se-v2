import datetime
import flask
from teknologkoren_se_v2 import models, util, locale

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
@mod.route('/blog/page/<int:page>/')
def index(page):
    posts = (models.Post
             .query
             .filter(models.Post.published < datetime.datetime.utcnow())
             .order_by(models.Post.published.desc())
             )

    pagination = posts.paginate(page, 5)
    return flask.render_template('public/index.html',
                                 pagination=pagination,
                                 page=page)


@mod.route('/blog/<int:post_id>/')
@mod.route('/blog/<int:post_id>/<slug>/')
def view_post(post_id, slug=None):
    post = models.Post.query.get_or_404(post_id)

    if not post.published or post.published > datetime.datetime.utcnow():
        return flask.abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != post.content.slug:
        return flask.redirect(
            flask.url_for(
                'public.view_post',
                post_id=post.id,
                slug=post.content.slug
            )
        )

    return flask.render_template('public/view_post.html', post=post)


@mod.route('/events/', defaults={'page': 1})
@mod.route('/events/page/<int:page>')
def events(page):
    events = (models.Post
              .query
              .filter(
                  models.Post.published < datetime.datetime.utcnow(),
                  models.Post.is_event.is_(True)
              )
              .order_by(models.Post.published.desc())
              )

    pagination = events.paginate(page, 5)
    return flask.render_template('public/events.html',
                                 pagination=pagination,
                                 page=page)


def view_page_factory(endpoint):
    def view_page():
        page = (models.Page.query
                .filter_by(path=endpoint)
                .order_by(models.Page.revision.desc())
                .first_or_404()
                )

        template = 'public/{}.html'.format(endpoint)
        return flask.render_template(template, page=page)

    return (endpoint, endpoint, view_page)


def init_dynamic_pages():
    pages = ['about', 'hire', 'apply', 'lucia']
    for page in pages:
        view_func = view_page_factory(page)
        mod.add_url_rule(*view_func)
