import datetime
import flask
import phonenumbers
import sqlalchemy as sqla
from sqlalchemy.ext.hybrid import hybrid_property
import flask_sqlalchemy
import slugify
import markdown
import flask_login
from teknologkoren_se_v2 import util
from teknologkoren_se_v2.locale import get_string, get_locale

db = flask_sqlalchemy.SQLAlchemy()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    published = db.Column(db.DateTime, nullable=True)

    title_sv = db.Column(db.String(100), nullable=False)
    title_en = db.Column(db.String(100), nullable=True)

    slug_sv = db.Column(db.String(200), nullable=False)
    slug_en = db.Column(db.String(200), nullable=True)

    text_sv = db.Column(db.Text, nullable=False)
    text_en = db.Column(db.Text, nullable=True)

    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', foreign_keys=image_id)

    type = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'post',
        'polymorphic_on': type
    }

    @property
    def title(self):
        lang = get_locale()

        if lang == 'sv':
            return self.title_sv

        if lang == 'en':
            return self.title_en or self.title_sv

        flask.abort(500)

    @property
    def text(self):
        lang = get_locale()

        if lang == 'sv':
            return self.text_sv

        if lang == 'en':
            return self.text_en or self.text_sv

        flask.abort(500)

    def html(self, offset=2):
        return markdown.markdown(
            self.text,
            extensions=['teknologkoren_se_v2.lib.mdx_headdown'],
            extension_configs={
                'mdx_headdown': {
                    'offset': offset
                }
            }
        )

    @property
    def url(self):
        """Return the path to the post."""
        return flask.url_for('public.post', id=self.id)

    @property
    def slug(self):
        lang = get_locale()

        if lang == 'sv':
            return self.slug_sv

        if lang == 'en':
            return self.slug_en or self.slug_sv

        flask.abort(500)

    def __str__(self):
        """String representation of the post."""
        return "<{} {}/{}>".format(
            self.__class__.__name__, self.id, self.slug
        )


class BlogPost(Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'blog_post'
    }


class Event(Post):
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)

    start_time = db.Column(db.DateTime, nullable=False)

    time_text_sv = db.Column(db.Text, nullable=True)
    time_text_en = db.Column(db.Text, nullable=True)

    location_sv = db.Column(db.String(100), nullable=False)
    location_en = db.Column(db.String(100), nullable=True)

    location_link = db.Column(db.String(500), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    @property
    def location(self):
        lang = get_locale()

        if lang == 'sv':
            return self.location_sv

        if lang == 'en':
            return self.location_en or self.location_sv

        flask.abort(500)

    @property
    def time_text(self):
        lang = get_locale()

        if lang == 'sv':
            return self.time_text_sv

        if lang == 'en':
            return self.time_text_en or self.time_text_sv

        flask.abort(500)

    @property
    def time_html(self):
        return markdown.markdown(
            self.time_text,
            extensions=['teknologkoren_se_v2.lib.mdx_headdown'],
            extension_configs={
                'mdx_headdown': {
                    'offset': 2
                }
            }
        )


@sqla.event.listens_for(Post.title_sv, 'set', propagate=True)
def create_slug_sv(target, value, oldvalue, initiator):
    target.slug_sv = slugify.slugify(value)


@sqla.event.listens_for(Post.title_en, 'set', propagate=True)
def create_slug_en(target, value, oldvalue, initiator):
    if value:
        target.slug_en = slugify.slugify(value)
    else:
        target.slug_en = None


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(50), nullable=False)
    text_sv = db.Column(db.Text, nullable=False)
    text_en = db.Column(db.Text, nullable=False)
    revision = db.Column(db.DateTime, nullable=False)

    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', foreign_keys=image_id)

    @property
    def text(self):
        lang = get_locale()

        if lang == 'sv':
            return self.text_sv

        if lang == 'en':
            return self.text_en or self.text_sv

        flask.abort(500)

    @property
    def html(self):
        return markdown.markdown(self.text)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)


class Contact(db.Model):
    """Should be the board (+ webmaster if you're feeling like it).

    An email address cannot be longer than 254 characters:
    http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(254), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.Integer, nullable=False)

    @property
    def formatted_phone(self):
        """Returns formatted number or False if not a valid number."""
        try:
            # If no country code, assume Swedish
            parsed = phonenumbers.parse(self.phone, 'SE')
        except phonenumbers.phonenumberutil.NumberParseException:
            return None

        if not (phonenumbers.is_possible_number(parsed) and
                phonenumbers.is_valid_number(parsed)):
            return None

        formatted = phonenumbers.format_number(
            parsed,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

        return formatted

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class AdminUser(flask_login.UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

    # Do not change the following directly, use AdminUser.password
    _password_hash = db.Column(db.String(256), nullable=False)
    _password_timestamp = db.Column(db.DateTime)

    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, plaintext):
        self._password_hash = (
            util.bcrypt
            .generate_password_hash(plaintext, 12)
            .decode()
        )

        self._password_timestamp = datetime.datetime.utcnow()

    def verify_password(self, plaintext):
        """Return True if plaintext matches password, else False."""
        correct = util.bcrypt.check_password_hash(
            self._password_hash,
            plaintext
        )

        return correct

    @staticmethod
    def authenticate(username, password):
        user = AdminUser.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            return user

        return None
