import flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import fields, validators, widgets
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


class RedirectForm(FlaskForm):
    next = fields.HiddenField()

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
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


class UploadForm(FlaskForm):
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

    published = html5_fields.DateTimeLocalField(
        'Publicerad',
        description=(
            "Vilken tid inlägget ska publiceras. Lämna tomt för att inte "
            "publicera."
        ),
        format='%Y-%m-%d %H:%M',
        render_kw={'placeholder': 'YYYY-mm-dd HH:MM'},
        validators=[
            validators.Optional()
        ]
    )


class EditEventForm(EditPostForm):
    start_time = html5_fields.DateTimeLocalField(
        'Tid',
        description=(
            "Om tidsbeskrivning lämnas tomt så syns denna som tid "
            "(automatiskt formaterat), annars göms den och används bara för "
            "att sortera händelserna."
        ),
        format='%Y-%m-%d %H:%M',
        render_kw={'placeholder': 'YYYY-mm-dd HH:MM'},
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


class EditPageForm(UploadForm):
    text_sv = fields.TextAreaField('Text', validators=[
        validators.InputRequired()
    ])
    text_en = fields.TextAreaField('Text', validators=[
        validators.InputRequired()
    ])


class EditFrontpageForm(FlaskForm):
    frontpage_image = fields.FormField(UploadForm)

    flash_sv = fields.StringField(
        'Flash',
        description=(
            'Text i flashen. Kan innehålla html, som '
            '<a href="https://example.com">en länk</a>.'
        )
    )
    flash_en = fields.StringField('Flash (engelska)')

    flash_type = fields.SelectField(
        'Flash-typ',
        description='Vilken färg flashen har',
        choices=[
            ('success', 'Grön'),
            ('warning', 'Gul'),
            ('error', 'Röd'),
            ('info', 'Blå')
        ]
    )


class EditContactForm(FlaskForm):
    title = fields.StringField(
        'Titel',
        validators=[
            validators.InputRequired()
        ]
    )
    name = fields.StringField(
        'Namn',
        validators=[
            validators.InputRequired()
        ]
    )
    email = fields.StringField(
        'E-postadress',
        validators=[
            validators.InputRequired()
        ]
    )
    phone = fields.StringField(
        'Telefonnummer',
        validators=[
            validators.Optional()
        ]
    )
    weight = fields.IntegerField(
        'Sorteringsvikt',
        validators=[
            validators.InputRequired()
        ]
    )


class NewUserForm(FlaskForm):
    username = fields.StringField(
        'Användarnamn',
        render_kw={'placeholder': "Ny användare"}
    )
    password = fields.PasswordField(
        'Lösenord',
        validators=[
            validators.Optional(),
            validators.Length(
                8,
                message="Åtminstone 8 tecken långa lösenord, tack!"
            )
        ]
    )


def editUserFormFactory(user):
    class F(FlaskForm):
        pass

    F.username = fields.StringField(
        'Användarnamn',
        default=user.username,
        render_kw={'placeholder': user.username},
        validators=[
            validators.InputRequired()
        ]
    )
    F.password = fields.PasswordField(
        'Lösenord',
        validators=[
            validators.Optional(),
            validators.Length(8)
        ]
    )
    F.delete = fields.BooleanField()
    return F


def editUsersFormFactory(users):
    class F(FlaskForm):
        pass

    for user in users:
        editUserForm = editUserFormFactory(user)
        form_name = f"user-{user.id}"
        setattr(F, form_name, fields.FormField(editUserForm))

    setattr(F, "new-user", fields.FormField(NewUserForm))
    return F
