import flask
import flask_wtf
from flask_wtf.file import FileAllowed
from wtforms import fields, validators
from wtforms.fields import html5 as html5_fields
from teknologkoren_se import models, util
from teknologkoren_se.locale import get_string


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


def none_if_space(data):
    if isinstance(data, str) and data.isspace():
        return None
    return data


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


class UploadForm(flask_wtf.FlaskForm):
    image = fields.FileField('Ladda upp ny bild', validators=[
        FileAllowed(util.image_uploads, 'Endast bilder!')
    ])
    portrait = fields.BooleanField(
        'Porträttläge',
        description="Bilden hamnar till höger om texten istället för ovanför"
    )


class EditPostForm(UploadForm):
    text_sv = fields.TextAreaField('Text', validators=[
        validators.InputRequired()
    ])
    text_en = fields.TextAreaField('Text', validators=[
        validators.Optional()
    ])

    title_sv = fields.StringField('Titel', validators=[
        validators.InputRequired()
    ])
    title_en = fields.StringField('Titel', validators=[
        validators.Optional()
    ])

    published = html5_fields.DateTimeField(
        'Publicerad',
        description=(
            "Vilken tid inlägget ska publiceras. Lämna tomt för att inte "
            "publicera."
        ),
        validators=[
            validators.Optional()
        ]
    )


class EditEventForm(EditPostForm):
    start_time = html5_fields.DateTimeField(
        'Tid',
        description=(
            "Om tidsbeskrivning lämnas tomt så syns denna som tid, annars "
            "göms den och används bara för att sortera händelserna."
        ),
        format='%Y-%m-%d %H:%M',
        validators=[
            validators.InputRequired()
        ]
    )

    time_text_sv = fields.TextAreaField(
        'Tidsbeskrivning',
        description=(
            "Beskrivning av tid i fritext (markdown). Om denna fylls i syns "
            "den istället för \"Tid\"."
        ),
        validators=[
            validators.Optional()
        ]
    )
    time_text_en = fields.TextAreaField(
        'Tidsbeskrivning',
        description=(
            "Beskrivning av tid i fritext (markdown). Om denna fylls i syns "
            "den istället för \"Tid\"."
        ),
        validators=[
            validators.Optional()
        ]
    )

    location_sv = fields.StringField('Plats', validators=[
        validators.InputRequired()
    ])
    location_en = fields.StringField('Plats', validators=[
        validators.Optional()
    ])

    location_link = fields.StringField('Länk till plats', validators=[
        validators.Optional()
    ])
