import flask
import flask_login
import pytz
from teknologkoren_se import models, util, locale, forms
from teknologkoren_se.locale import get_string

mod = flask.Blueprint(
    'admin',
    __name__,
    url_prefix='/<any(sv, en):lang_code>/admin'
)

locale.bp_url_processors(mod)

login_manager = flask_login.LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'


def setup_jinja(app):
    app.jinja_env.globals['url_for_other_page'] = util.url_for_other_page
    app.jinja_env.globals['image_url'] = util.image_uploads.url
    app.jinja_env.globals['image_dest'] = lambda: (util
                                                   .image_uploads
                                                   .config
                                                   .base_url)


def cet_to_utc(dt):
    tz = pytz.timezone('Europe/Stockholm')
    utc = tz.localize(dt, is_dst=None).astimezone(pytz.utc)
    return utc


def utc_to_cet(dt):
    tz = pytz.timezone('Europe/Stockholm')
    cet = pytz.utc.localize(dt, is_dst=None).astimezone(tz)
    return cet


@login_manager.user_loader
def load_user(user_id):
    """Tell flask-login how to get logged in user."""
    return models.AdminUser.query.get(user_id)


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
            return flask.render_template('admin/login.html', form=form)

        flask_login.login_user(user, remember=form.remember.data)
        return form.redirect('admin.index')

    return flask.render_template('admin/login.html', form=form)


@mod.route('/logout')
def logout():
    if flask_login.current_user.is_authenticated:
        flask_login.logout_user()

    return flask.redirect(flask.url_for('public.index'))


@flask_login.login_required
@mod.route('/')
def index():
    pages = models.Page.query.all()
    posts = models.BlogPost.query.order_by(models.BlogPost.id.desc()).all()
    events = models.Event.query.order_by(models.Event.id.desc()).all()
    return flask.render_template(
        'admin/index.html',
        pages=pages,
        posts=posts,
        events=events
    )


@flask_login.login_required
@mod.route('/frontpage', methods=['GET', 'POST'])
def frontpage():
    config = models.Config.query.first()

    form = forms.EditFrontpageForm(obj=config)

    if form.validate_on_submit():
        if form.frontpage_image.image.data:
            filename = util.image_uploads.save(form.frontpage_image.image.data)
            image = models.Image(
                filename=filename,
                portrait=False
            )
            models.db.session.add(image)

            config.frontpage_image = image

        config.flash = forms.none_if_space(form.flash.data)
        config.flash_type = form.flash_type.data

        models.db.session.commit()

        flask.flash("Uppdaterad!", 'success')

        return flask.redirect(flask.url_for('admin.frontpage'))

    else:
        forms.flash_errors(form)

    return flask.render_template(
        'admin/frontpage.html',
        config=config,
        form=form
    )


@flask_login.login_required
@mod.route('/contacts', methods=['GET', 'POST'])
def contacts():
    contacts = (
        models.Contact
        .query
        .order_by(models.Contact.weight.desc())
        .all()
    )

    return flask.render_template(
        'admin/contacts.html',
        contacts=contacts,
    )


@flask_login.login_required
@mod.route('/contacts/new', methods=['GET', 'POST'])
@mod.route('/contacts/<int:contact_id>', methods=['GET', 'POST'])
def edit_contact(contact_id=None):
    if contact_id:
        contact = models.Contact.query.get_or_404(contact_id)
    else:
        contact = None

    form = forms.EditContactForm(obj=contact)

    if form.validate_on_submit():
        if not contact_id:
            contact = models.Contact()

        contact.title = form.title.data
        contact.first_name = form.first_name.data
        contact.last_name = form.last_name.data
        contact.email = form.email.data
        contact.phone = form.phone.data
        contact.weight = form.weight.data

        if not contact_id:
            models.db.session.add(contact)

        models.db.session.commit()

        if not contact_id:
            flask.flash("Kontakt tillagd!", 'success')
        else:
            flask.flash("Kontakt ändrad!", 'success')

        return flask.redirect(flask.url_for('admin.contacts'))
    else:
        forms.flash_errors(form)

    return flask.render_template(
        'admin/edit_contact.html',
        form=form,
        contact=contact
    )


@flask_login.login_required
@mod.route('/contacts/<int:contact_id>/remove')
def delete_contact(contact_id):
    contact = models.Contact.query.get_or_404(contact_id)
    title = contact.title
    models.db.session.delete(contact)
    models.db.session.commit()

    flask.flash("Kontakt {} borttagen!".format(title), 'success')
    return flask.redirect(flask.url_for('admin.index'))


@flask_login.login_required
@mod.route('/post/new', methods=['GET', 'POST'])
@mod.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id=None):
    if post_id:
        post = models.BlogPost.query.get_or_404(post_id)
    else:
        post = None

    form = forms.EditPostForm(obj=post)

    if form.validate_on_submit():
        if not post:
            post = models.BlogPost()

        published_cet = forms.none_if_space(form.published.data)
        if published_cet:
            published = cet_to_utc(published_cet)
        else:
            published = None

        post.published = published

        post.title_sv = form.title_sv.data
        post.title_en = forms.none_if_space(form.title_en.data)

        post.text_sv = form.text_sv.data
        post.text_en = forms.none_if_space(form.text_en.data)

        if form.image.data:
            filename = util.image_uploads.save(form.image.data)
            image = models.Image(filename=filename)
            models.db.session.add(image)

            image.portrait = form.portrait.data
            post.image = image

        elif post.image:
            post.image.portrait = form.portrait.data

        if not post_id:
            models.db.session.add(post)

        models.db.session.commit()

        if post_id:
            flask.flash("Uppdaterad!", 'success')
        else:
            flask.flash("Inlägg skapat!", 'success')

        return flask.redirect(flask.url_for('admin.post', post_id=post.id))

    else:
        forms.flash_errors(form)

    if post and post.image:
        form.portrait.data = post.image.portrait

    return flask.render_template('admin/post.html', post=post, form=form)


@flask_login.login_required
@mod.route('/event/new', methods=['GET', 'POST'])
@mod.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event(event_id=None):
    if event_id:
        event = models.Event.query.get(event_id)
    else:
        event = None

    form = forms.EditEventForm(obj=event)

    if form.validate_on_submit():
        if not event:
            event = models.Event()

        published_cet = forms.none_if_space(form.published.data)
        if published_cet:
            published = cet_to_utc(published_cet)
        else:
            published = None

        event.published = published

        event.title_sv = form.title_sv.data
        event.title_en = forms.none_if_space(form.title_en.data)

        event.text_sv = form.text_sv.data
        event.text_en = forms.none_if_space(form.text_en.data)

        event.start_time = cet_to_utc(form.start_time.data)

        event.time_text_sv = forms.none_if_space(form.time_text_sv.data)
        event.time_text_en = forms.none_if_space(form.time_text_en.data)

        event.location_sv = form.location_sv.data
        event.location_en = forms.none_if_space(form.location_en.data)

        event.location_link = forms.none_if_space(form.location_link.data)

        if form.image.data:
            filename = util.image_uploads.save(form.image.data)
            image = models.Image(filename=filename)
            models.db.session.add(image)

            image.portrait = form.portrait.data
            event.image = image

        elif event.image:
            event.image.portrait = form.portrait.data

        if not event_id:
            models.db.session.add(event)

        models.db.session.commit()

        if event_id:
            flask.flash("Uppdaterad!", 'success')
        else:
            flask.flash("Händelse skapad!", 'success')

        return flask.redirect(flask.url_for('admin.event', event_id=event.id))

    else:
        forms.flash_errors(form)

    if event and event.image:
        form.portrait.data = event.image.portrait

    return flask.render_template('admin/event.html', event=event, form=form)


@flask_login.login_required
@mod.route('/post/<int:post_id>/remove')
def delete_post(post_id):
    post = models.BlogPost.query.get_or_404(post_id)
    post_title = post.title_sv
    models.db.session.delete(post)
    models.db.session.commit()

    flask.flash("Inlägg {} borttaget!".format(post_title), 'success')
    return flask.redirect(flask.url_for('admin.index'))


@flask_login.login_required
@mod.route('/event/<int:event_id>/remove')
def delete_event(event_id):
    event = models.Event.query.get_or_404(event_id)
    event_title = event.title_sv
    models.db.session.delete(event)
    models.db.session.commit()

    flask.flash("Händelse {} borttagen!".format(event_title), 'success')
    return flask.redirect(flask.url_for('admin.index'))


@flask_login.login_required
@mod.route('/page/<int:page_id>', methods=['GET', 'POST'])
def page(page_id=None):
    if page_id:
        page = models.Page.query.get_or_404(page_id)
    else:
        page = None

    form = forms.EditPageForm(obj=page)

    if form.validate_on_submit():
        page.text_sv = form.text_sv.data
        page.text_en = form.text_en.data

        if form.image.data:
            filename = util.image_uploads.save(form.image.data)
            image = models.Image(
                filename=filename,
                portrait=form.portrait.data
            )
            models.db.session.add(image)

            page.image = image

        models.db.session.commit()

        flask.flash("Uppdaterad!", 'success')

        return flask.redirect(flask.url_for('admin.page', page_id=page.id))

    else:
        forms.flash_errors(form)

    return flask.render_template('admin/page.html', page=page, form=form)
