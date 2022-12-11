import flask
from werkzeug.exceptions import MethodNotAllowed, NotFound
from werkzeug.routing import RequestRedirect

from teknologkoren_se.translations import translations


class LazyTranslation:
    """For use in things working outside application context.

    Forms are initialized before an application context has been
    created which means we can't use get_locale() as that fetches
    the locale from g or the session (which require an application
    context). By putting get_locale() in __str__(), we postpone the
    call to get_locale() until the string is actually rendered.
    """

    def __init__(self, translation):
        self.translation = translation

    def __str__(self):
        return self.translation[get_locale()]


def get_string(name, lazy=False):
    translation = translations.get(name)
    if translation:
        if lazy:
            return LazyTranslation(translation)
        else:
            return translations[name][get_locale()]
    else:
        return name


def get_locale():
    lang_code = flask.g.get('lang_code') or flask.session.get('lang_code')

    if not lang_code:
        lang_code = (
            flask.request.accept_languages.best_match(['sv', 'en'], 'sv')
        )

    return lang_code


def fix_missing_lang_code():
    if flask.g.get('lang_code') or flask.request.endpoint == 'static':
        # Lang code is not missing.
        return

    # If g.lang_code is not set, the lang code in path is probably
    # missing or misspelled/invalid.

    # Get a MapAdapter, the object used for matching urls.
    urls = flask.current_app.url_map.bind(
        flask.current_app.config['SERVER_NAME']
    )

    # Get whatever lang get_locale() decides (cookie or, if no cookie,
    # default), and prepend it to the requested path.
    proposed_lang = get_locale()
    new_path = proposed_lang + flask.request.path

    try:
        # Does this new path match any view?
        urls.match(new_path)
    except RequestRedirect as e:
        # The new path results in a redirect.
        return flask.redirect(e.new_url)
    except (MethodNotAllowed, NotFound):
        # The new path does not match anything, we allow the request
        # to continue with the non-lang path. Probably 404. In case
        # this request results in something that does want a lang
        # code, we set it to whatever was proposed by get_locale().
        # If we don't set it AND the client does not have lang saved
        # in a cookie, we'd get a 500.
        flask.g.lang_code = proposed_lang
        return None

    # The new path matches a view! We redirect there.
    return flask.redirect(new_path)


def url_for_lang(endpoint, lang_code, view_args, fallback='index.index', **args):
    view_args = view_args or {}
    url_map = flask.current_app.url_map

    if endpoint and url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        return flask.url_for(endpoint, lang_code=lang_code, **view_args, **args)

    return flask.url_for(fallback, lang_code=lang_code, **view_args, **args)


def bp_url_processors(bp):
    @bp.url_defaults
    def add_language_code(endpoint, values):
        if not values.get('lang_code'):
            values['lang_code'] = (flask.g.get('lang_code')
                                   or flask.session.get('lang_code'))

    @bp.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        lang_code = values.pop('lang_code')

        if lang_code in ('sv', 'en'):
            # Valid lang_code, set the global lang_code and cookie
            flask.g.lang_code = lang_code
            flask.session['lang_code'] = lang_code
