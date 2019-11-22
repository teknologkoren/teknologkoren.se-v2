import flask
import flask_wtf
from wtforms import fields, validators
from teknologkoren_se_v2 import models, util
from teknologkoren_se_v2.locale import get_string


def flash_errors(form):
    """Flash all errors in a form."""
    for field in form:
        if isinstance(field, (fields.FormField, fields.FieldList)):
            flash_errors(field)
            continue

        for error in field.errors:
            flask.flash(
                get_string('field-error').format(field.label.text, error),
                'error'
            )


class Unique:
    """Validate that field is unique in model."""
    def __init__(self, model, field,
                 message=get_string("this element already exists")):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if (models.db.session.query(self.model)
                .filter(self.field == field.data).scalar()):
            raise validators.ValidationError(self.message)


class Exists:
    """Validate that field exists in model."""
    def __init__(self, model, field,
                 message=get_string("that element doesn't exists")):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if not (models.db.session.query(self.model)
                .filter(self.field == field.data).scalar()):
            raise validators.ValidationError(self.message)


class RedirectForm(flask_wtf.FlaskForm):
    next = fields.HiddenField()

    def __init__(self, *args, **kwargs):
        flask_wtf.FlaskForm.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = util.get_redirect_target() or ''

    def redirect(self, endpoint='admin.index', **values):
        if self.next.data and util.is_safe_url(self.next.data):
            return flask.redirect(self.next.data)
        target = util.get_redirect_target()
        return flask.redirect(target or flask.url_for(endpoint, **values))


class LoginForm(RedirectForm):
    remember = fields.BooleanField(get_string('remember-me', lazy=True))
    username = fields.StringField(
        get_string('username', lazy=True),
        validators=[validators.InputRequired()]
    )
    password = fields.PasswordField(
        get_string('password', lazy=True),
        validators=[validators.InputRequired()]
    )
