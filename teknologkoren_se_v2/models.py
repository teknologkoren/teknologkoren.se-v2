import flask
import phonenumbers
import sqlalchemy as sqla
import flask_sqlalchemy
import slugify
import markdown
from teknologkoren_se_v2.locale import get_string, get_locale

db = flask_sqlalchemy.SQLAlchemy()


class Post(db.Model):
    """This is only meta data, the content is in {Post,Event}Content."""
    id = db.Column(db.Integer, primary_key=True)
    published = db.Column(db.DateTime, nullable=True)
    is_event = db.Column(db.Boolean, nullable=False)

    @property
    def content(self):
        content = (PostContent.query
                   .filter(PostContent.post_id == self.id)
                   .order_by(PostContent.timestamp.desc())
                   .first()
                   )
        return content

    @property
    def url(self):
        """Return the path to the post."""
        return flask.url_for('public.post', id=self.id)

    def __str__(self):
        """String representation of the post."""
        return "<{} {}/{}>".format(self.__class__.__name__, self.id, self.slug)


class PostContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_sv = db.Column(db.String(100), nullable=False)
    title_en = db.Column(db.String(100), nullable=True)
    slug_sv = db.Column(db.String(200), nullable=False)
    slug_en = db.Column(db.String(200), nullable=True)
    text_sv = db.Column(db.Text, nullable=False)
    text_en = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', foreign_keys=post_id, backref='contents')

    type = db.Column(db.String(20))
    __mapper_args__ = {
        'polymorphic_identity': 'post_content',
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
            return (self.text_en or
                    get_string('no translation') + self.text_sv)

        flask.abort(500)

    @property
    def html(self):
        return markdown.markdown(self.text)

    @property
    def slug(self):
        lang = get_locale()

        if lang == 'sv':
            return self.slug_sv

        if lang == 'en':
            return self.slug_en or self.slug_sv

        flask.abort(500)


class EventContent(PostContent):
    # Tell flask-sqlalchemy not to create a table for this class.
    # single table inheritance with PostContent, same table as
    # PostContent.
    __table_name__ = None

    start_time = db.Column(db.DateTime)
    location_sv = db.Column(db.String(100))
    location_en = db.Column(db.String(100))
    location_link = db.Column(db.String(500), nullable=True)

    @property
    def location(self):
        lang = get_locale()

        if lang == 'sv':
            return self.location_sv

        if lang == 'en':
            return self.location_en or self.location_en

        flask.abort(500)

    __mapper_args__ = {
        'polymorphic_identity': 'event_content'
    }


@sqla.event.listens_for(PostContent.title_sv, 'set', propagate=True)
def create_slug_sv(target, value, oldvalue, initiator):
    """Create slug when new title is set.
    Listens for PostContent and subclasses of PostContent.
    """
    target.slug_sv = slugify.slugify(value)


@sqla.event.listens_for(PostContent.title_en, 'set', propagate=True)
def create_slug_en(target, value, oldvalue, initiator):
    """Create slug when new title is set.
    Listens for PostContent and subclasses of PostContent.
    """
    target.slug_en = slugify.slugify(value)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post_content.id'),
                        nullable=False)

    post = db.relationship('PostContent',
                           foreign_keys=post_id,
                           backref='images')


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
