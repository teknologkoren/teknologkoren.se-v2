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
@mod.route('/page/<int:page>/')
def index(page):
    posts = (models.Post
             .query
             .filter(models.Post.published < datetime.datetime.utcnow())
             .order_by(models.Post.published.desc())
             )

    pagination = posts.paginate(page, 5)
    return flask.render_template('index.html',
                                 pagination=pagination,
                                 page=page)


@mod.route('/post/<int:post_id>/')
@mod.route('/post/<int:post_id>/<slug>/')
def view_post(post_id, slug=None):
    post = models.Post.query.get_or_404(post_id)

    if not post.published or post.published < datetime.datetime.utcnow():
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

    return flask.render_template('public/view-post.html', post=post)
