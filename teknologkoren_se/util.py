import flask
import flask_uploads
from urllib.parse import urlparse, urljoin

image_uploads = flask_uploads.UploadSet('images', flask_uploads.IMAGES)


def url_for_other_page(page):
    """Return url for a page number."""
    args = flask.request.view_args.copy()
    args['page'] = page
    return flask.url_for(flask.request.endpoint, **args)


def url_for_image(filename, width=None):
    base = image_uploads.config.base_url

    if width and not flask.current_app.debug:
        url = urljoin(base, 'img{}/{}'.format(width, filename))
    else:
        url = urljoin(base, filename)

    return url


def is_safe_url(target):
    """Tests if the url is a safe target for redirection.

    Does so by checking that the url is still using http or https and
    and that the url is still our site.
    """
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        test_url.netloc == ref_url.netloc


def get_redirect_target():
    """Get where we want to redirect to.

    Checks the 'next' argument in the request and if nothing there, use
    the http referrer. Also checks whether the target is safe to
    redirect to (no 'open redirects').
    """
    for target in (flask.request.values.get('next'), flask.request.referrer):
        if not target:
            continue
        if target == flask.request.url:
            continue
        if is_safe_url(target):
            return target
