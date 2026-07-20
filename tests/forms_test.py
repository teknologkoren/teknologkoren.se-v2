import datetime

import flask
import pytest
from flask_wtf import FlaskForm

from teknologkoren_se import forms, models
from tests.helpers import make_contact

# The app and client pytest fixtures live in tests/conftest.py.


def make_image(filename):
    """Create an image db row (no actual file), commit it and return it."""
    image = models.Image(filename=filename, portrait=False)
    models.db.session.add(image)
    models.db.session.commit()
    return image


# none_if_space

def test_none_if_space_only_spaces_becomes_none():
    assert forms.none_if_space(' ') is None
    assert forms.none_if_space('   ') is None
    assert forms.none_if_space('\t\n ') is None


def test_none_if_space_keeps_text():
    assert forms.none_if_space('hej') == 'hej'
    assert forms.none_if_space(' hej ') == ' hej '


def test_none_if_space_empty_string_passes_through():
    # ''.isspace() is False, so the empty string is *not* converted to
    # None. Views relying on none_if_space store '' in nullable columns
    # when a field is submitted empty.
    assert forms.none_if_space('') == ''


def test_none_if_space_non_strings_pass_through():
    assert forms.none_if_space(None) is None
    dt = datetime.datetime(2020, 1, 1, 12, 0)
    assert forms.none_if_space(dt) is dt


# choose_image_field

def test_choose_image_field_choices_and_default(app):
    img_a = make_image('a.png')
    img_b = make_image('b.png')

    class F(FlaskForm):
        choose_image = forms.choose_image_field(
            [img_a, img_b], current_choice_id=img_a.id
        )

    with app.test_request_context('/'):
        form = F()

    # "None" first, then the images in reverse order (newest first).
    assert form.choose_image.choices == [
        (-1, 'None'),
        (img_b.id, 'b.png'),
        (img_a.id, 'a.png'),
    ]
    assert form.choose_image.default == img_a.id
    # RadioField coerces to str by default.
    assert form.choose_image.data == str(img_a.id)


def test_choose_image_field_defaults_to_none_choice(app):
    class F(FlaskForm):
        choose_image = forms.choose_image_field([], current_choice_id=None)

    with app.test_request_context('/'):
        form = F()

    assert form.choose_image.choices == [(-1, 'None')]
    assert form.choose_image.default == -1
    assert form.choose_image.data == '-1'


# flash_errors

def test_flash_errors_flashes_field_errors(app):
    with app.test_request_context('/sv/login', method='POST', data={}):
        form = forms.LoginForm()
        assert form.validate() is False
        forms.flash_errors(form)
        messages = flask.get_flashed_messages(with_categories=True)

    # Both username and password are required.
    assert len(messages) == 2
    assert all(category == 'error' for category, _ in messages)


def test_flash_errors_recurses_into_nested_forms(app):
    contact = make_contact()
    F = forms.editContactsFormFactory([contact])

    data = {
        # The existing contact's subform is valid...
        f'contact-{contact.id}-title': contact.title,
        f'contact-{contact.id}-name': contact.name,
        f'contact-{contact.id}-email': contact.email,
        f'contact-{contact.id}-phone': contact.phone,
        f'contact-{contact.id}-weight': str(contact.weight),
        # ...but the new-contact subform is only partially filled in,
        # so its name, email and weight fields all fail validation.
        'new-contact-title': 'Sekreterare',
    }

    with app.test_request_context('/admin/contacts', method='POST',
                                  data=data):
        form = F()
        assert form.validate() is False
        forms.flash_errors(form)
        messages = flask.get_flashed_messages(with_categories=True)

    assert len(messages) == 3
    assert all(category == 'error' for category, _ in messages)
    flashed_text = ' '.join(message for _, message in messages)
    # The errors mention the nested fields' labels.
    assert 'Namn' in flashed_text
    assert 'E-postadress' in flashed_text
    assert 'Sorteringsvikt' in flashed_text


# editContactsFormFactory

def test_edit_contacts_form_has_one_subform_per_contact(app):
    first = make_contact(title='Ordförande', name='Monty Python',
                         weight=100)
    second = make_contact(title='Kassör', name='Terry Gilliam',
                          email='pengar@teknologkoren.se', weight=50)

    F = forms.editContactsFormFactory([first, second])
    with app.test_request_context('/admin/contacts'):
        form = F()

    field_names = [field.name for field in form]
    assert f'contact-{first.id}' in field_names
    assert f'contact-{second.id}' in field_names
    assert 'new-contact' in field_names

    # The subforms default to the contacts' current data.
    sub_form = form[f'contact-{first.id}']
    assert sub_form.form.title.data == 'Ordförande'
    assert sub_form.form.name.data == 'Monty Python'
    assert sub_form.form.email.data == 'ordf@teknologkoren.se'
    assert sub_form.form.weight.data == 100
    assert sub_form.form.delete.data is False

    # The nested fields get FormField-prefixed html names.
    assert sub_form.form.title.name == f'contact-{first.id}-title'
    new_contact = form['new-contact']
    assert new_contact.form.name.name == 'new-contact-name'


# editUsersFormFactory

def test_edit_users_form_has_one_subform_per_user(app):
    monty = models.AdminUser(username='monty', password='spamspamspam')
    brian = models.AdminUser(username='brian', password='spamspamspam')
    models.db.session.add_all([monty, brian])
    models.db.session.commit()

    F = forms.editUsersFormFactory([monty, brian])
    with app.test_request_context('/admin/users'):
        form = F()

    field_names = [field.name for field in form]
    assert f'user-{monty.id}' in field_names
    assert f'user-{brian.id}' in field_names
    assert 'new-user' in field_names

    sub_form = form[f'user-{monty.id}']
    assert sub_form.form.username.data == 'monty'
    # The password field is left empty (only set to change password).
    assert not sub_form.form.password.data
    assert sub_form.form.delete.data is False
    assert sub_form.form.username.name == f'user-{monty.id}-username'

    new_user = form['new-user']
    assert new_user.form.username.name == 'new-user-username'
    assert new_user.form.password.name == 'new-user-password'


# OptionalForm

def test_optional_form_empty_passes_without_validation(app):
    F = forms.newContactFormFactory()
    with app.test_request_context('/admin/contacts', method='POST',
                                  data={}):
        form = F()
        assert form.validate() is True
    assert form.filled_in is False


def test_optional_form_partially_filled_validates_normally(app):
    F = forms.newContactFormFactory()
    with app.test_request_context('/admin/contacts', method='POST',
                                  data={'title': 'Sekreterare'}):
        form = F()
        assert form.validate() is False

    assert form.filled_in is True
    assert form.name.errors
    assert form.email.errors
    assert form.weight.errors


def test_optional_form_fully_filled_validates(app):
    F = forms.newContactFormFactory()
    data = {
        'title': 'Sekreterare',
        'name': 'Hedda Hopper',
        'email': 'hedda@teknologkoren.se',
        'phone': '0711234567',
        'weight': '50',
    }
    with app.test_request_context('/admin/contacts', method='POST',
                                  data=data):
        form = F()
        assert form.validate() is True

    assert form.filled_in is True
    assert form.weight.data == 50


def test_optional_form_only_weight_filled_crashes(app):
    # KNOWN BUG (teknologkoren_se/forms.py:292): OptionalForm.validate()
    # calls value.strip() on every non-empty field value to decide
    # whether the form was filled in, but weight is an IntegerField
    # whose data is an int. Submitting the new-contact subform with
    # *only* the weight field filled in therefore raises AttributeError
    # (500 in production) instead of failing validation gracefully.
    # This test documents the current behavior; do not "fix" the test
    # if the bug is fixed -- update it to assert validate() is False.
    F = forms.newContactFormFactory()
    with app.test_request_context('/admin/contacts', method='POST',
                                  data={'weight': '50'}):
        form = F()
        with pytest.raises(AttributeError):
            form.validate()


def test_optional_form_validate_rejects_extra_validators(app):
    # UPGRADE HAZARD (teknologkoren_se/forms.py:285): OptionalForm
    # overrides validate() without the extra_validators parameter that
    # wtforms 3.x Form.validate() and flask-wtf's validate_on_submit()
    # pass. The app only validates OptionalForm through FormField, whose
    # validate() calls the enclosed form's validate() without arguments,
    # so this does not break anything under the currently pinned
    # versions -- but calling validate_on_submit() directly on an
    # OptionalForm raises TypeError, and a future wtforms/flask-wtf that
    # forwards extra_validators through FormField would break the
    # contacts view.
    F = forms.newContactFormFactory()
    with app.test_request_context('/admin/contacts', method='POST',
                                  data={}):
        form = F()
        with pytest.raises(TypeError):
            form.validate_on_submit()
