import flask
import flask_login
import pytz

from teknologkoren_se import forms, models, util

mod = flask.Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'
)

login_manager = flask_login.LoginManager()
login_manager.login_view = 'public.login'
login_manager.login_message_category = 'info'


def setup_jinja(app):
    app.jinja_env.globals['url_for_other_page'] = util.url_for_other_page
    app.jinja_env.globals['image_url'] = util.image_uploads.url
    app.jinja_env.globals['image_dest'] = lambda: util.image_uploads.config.base_url


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
    return models.AdminUser.query.get(user_id)


@mod.route('/logout')
def logout():
    # Login is in public view
    if flask_login.current_user.is_authenticated:
        flask_login.logout_user()
    return flask.redirect(flask.url_for('public.index'))


@mod.route('/')
@flask_login.login_required
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


@mod.route('/frontpage', methods=['GET', 'POST'])
@flask_login.login_required
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

        config.flash_sv = forms.none_if_space(form.flash_sv.data)
        config.flash_en = forms.none_if_space(form.flash_en.data)
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


@mod.route('/contacts', methods=['GET', 'POST'])
@flask_login.login_required
def contacts():
    contacts = (
        models.Contact.query.order_by(models.Contact.weight.desc()).all()
    )
    form = forms.editContactsFormFactory(contacts)()

    if form.validate_on_submit():
        for sub_form in form:
            if sub_form.name == 'csrf_token':
                continue

            if sub_form.name == 'new-contact':
                if sub_form.filled_in:
                    contact = models.Contact()
                else:
                    continue
            else:
                _, contact_id = sub_form.name.split('-')
                # 404 could happen if multiple users edit at the same
                # time or has edited the name of the form manually...
                contact = models.Contact.query.get_or_404(contact_id)

                if sub_form.delete.data:
                    models.db.session.delete(contact)
                    continue

            contact.title = sub_form.form.title.data
            contact.name = sub_form.form.name.data
            contact.email = sub_form.form.email.data
            contact.phone = sub_form.form.phone.data
            contact.weight = sub_form.form.weight.data

            if sub_form.name == 'new-contact':
                models.db.session.add(contact)

        models.db.session.commit()
        flask.flash("Kontaker sparade!", 'success')
        return flask.redirect(flask.url_for('admin.contacts'))
    else:
        forms.flash_errors(form)

    return flask.render_template('admin/contacts.html', form=form)


@mod.route('/post/new', methods=['GET', 'POST'])
@mod.route('/post/<int:post_id>', methods=['GET', 'POST'])
@flask_login.login_required
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

    # If form was submitted, display the new form data, else convert utc to cet
    # Gets converted back to utc from cet on submit that got through validation
    if post and post.published and not form.is_submitted():
        form.published.data = utc_to_cet(post.published)

    return flask.render_template('admin/post.html', post=post, form=form)


@mod.route('/event/new', methods=['GET', 'POST'])
@mod.route('/event/<int:event_id>', methods=['GET', 'POST'])
@flask_login.login_required
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

    # If form was submitted, display the new form data, else convert utc to cet
    # Gets converted back to utc from cet on submit that got through validation
    if event and not form.is_submitted():
        form.start_time.data = utc_to_cet(event.start_time)
        if event.published:
            form.published.data = utc_to_cet(event.published)

    return flask.render_template('admin/event.html', event=event, form=form)


@mod.route('/post/<int:post_id>/remove')
@flask_login.login_required
def delete_post(post_id):
    post = models.BlogPost.query.get_or_404(post_id)
    post_title = post.title_sv
    models.db.session.delete(post)
    models.db.session.commit()

    flask.flash("Inlägg {} borttaget!".format(post_title), 'success')
    return flask.redirect(flask.url_for('admin.index'))


@mod.route('/event/<int:event_id>/remove')
@flask_login.login_required
def delete_event(event_id):
    event = models.Event.query.get_or_404(event_id)
    event_title = event.title_sv
    models.db.session.delete(event)
    models.db.session.commit()

    flask.flash("Händelse {} borttagen!".format(event_title), 'success')
    return flask.redirect(flask.url_for('admin.index'))


@mod.route('/page/<int:page_id>', methods=['GET', 'POST'])
@flask_login.login_required
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


@mod.route('/users', methods=['GET', 'POST'])
@flask_login.login_required
def users():
    users = models.AdminUser.query.all()
    form = forms.editUsersFormFactory(users)()

    if form.validate_on_submit():
        for sub_form in form:
            if sub_form.name == 'csrf_token':
                continue

            if sub_form.name == 'new-user':
                username = sub_form.username.data.strip()
                if username:
                    if models.AdminUser.query.filter_by(username=username).first():
                        flask.flash(
                            "Användarnamnet \"{}\" är upptaget!".format(username),
                            'error'
                        )
                        return flask.render_template(
                            'admin/users.html',
                            form=form
                        )
                    if not sub_form.password.data:
                        flask.flash(
                            "Ange ett lösenord för den nya användaren!",
                            'error'
                        )
                        return flask.render_template(
                            'admin/users.html',
                            form=form
                        )
                else:
                    continue
                user = models.AdminUser(
                    username=sub_form.username.data.strip(),
                    password=sub_form.password.data
                )
                models.db.session.add(user)
            else:
                _, user_id = sub_form.name.split('-')
                # 404 will probably never happen lol
                # but better safe than sorry^W 500
                user = models.AdminUser.query.get_or_404(user_id)

                if sub_form.delete.data:
                    if user == flask_login.current_user:
                        flask.flash(
                            "Du kan inte ta bort användaren du är inloggad med!",
                            'error'
                        )
                        models.db.session.rollback()
                        return flask.render_template(
                            'admin/users.html',
                            form=form
                        )
                    models.db.session.delete(user)
                    continue

                user.username = sub_form.username.data
                if sub_form.password.data:
                    user.password = sub_form.password.data
        else:
            models.db.session.commit()
            return flask.redirect(flask.url_for('admin.users'))
    else:
        forms.flash_errors(form)

    return flask.render_template('admin/users.html', form=form)
