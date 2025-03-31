"""Admin views for the application."""
from urllib.parse import quote
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField
from flask_admin.form import Select2Widget
from markupsafe import Markup
from flask import session
from app import db
from app.models.models import OriginalSubscription, RedirectMapping, Settings, User
from flask import redirect, url_for, request, flash
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView



class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('admin_logged_in', False)

    def inaccessible_callback(self, name, **kwargs):
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('admin.login', next=request.url))


class OriginalSubscriptionView(SecureModelView):
    """Admin view for original subscriptions."""
    column_list = ('name', 'description', 'url', '_actions')
    column_labels = {
        'name': 'Profile Name',
        'description': 'Description',
        'url': 'Original Subscription URL',
        '_actions': 'Actions'
    }
    form_columns = ('name', 'description', 'url')

    column_formatters = {
        '_actions': lambda v, c, m, p: Markup(
            f'''
            <button class="btn btn-sm btn-primary" onclick="navigator.clipboard.writeText('{m.url}')">Copy Link</button>
            '''
        )
    }


class SubscriptionView(SecureModelView):
    """Admin view for generated subscriptions."""
    column_list = ['name', 'description', 'url', '_actions']
    column_labels = {
        'name': 'Complex Profile Name',
        'description': 'Description',
        'url': 'Converted Subscription URL',
        '_actions': 'Actions'
    }
    form_columns = ['name', 'description', 'original_subscriptions']

    column_formatters = {
        '_actions': lambda v, c, m, p: Markup(
            f'''
            <button class="btn btn-sm btn-primary" onclick="navigator.clipboard.writeText('{m.url}')">Copy Link</button>
            '''
        )
    }

    form_extra_fields = {
        'original_subscriptions': QuerySelectMultipleField(
            'Selected Original Subscriptions',
            query_factory=lambda: OriginalSubscription.query.all(),
            get_label='name',
            widget=Select2Widget(multiple=True)
        )
    }


    def on_model_change(self, form, model, is_created):
        """Handle subscription creation and updates."""

        selected_subscriptions = form.original_subscriptions.data

        if not selected_subscriptions:
            raise ValueError("At least one original subscription must be selected.")

        urls_to_merge = [sub.url for sub in selected_subscriptions]

        # Generate merged subscription URL
        subconverter_api = Settings.query.filter_by(key='subconverter_api').first().value
        base_url = Settings.query.filter_by(key='base_url').first().value
        urls_to_merge_str = quote("|".join(urls_to_merge))
        #urls_to_merge_str = "|".join(urls_to_merge)
        target_url = f"{subconverter_api}?target=clash&url={urls_to_merge_str}"

        # Create a friendly URL path
        formatted_name = model.name.replace(" ", "-").replace("&", "and").lower()
        model.url = f"{base_url}/sub/{formatted_name}"
        if is_created:
            db.session.flush()

        existing_mapping = RedirectMapping.query.filter_by(subscription_id=model.id).first()
        if existing_mapping:
            existing_mapping.unique_id = formatted_name
            existing_mapping.target_url = target_url
        else:
            redirect_mapping = RedirectMapping(
                unique_id=formatted_name,
                target_url=target_url,
                subscription_id=model.id
            )
            db.session.add(redirect_mapping)




class SettingsAdmin(SecureModelView):
    """Admin view for settings."""
    column_list = ['key', 'value', 'description']
    column_labels = {
        'key': 'Settings',
        'value': 'Value',
        'description': 'Description'
    }
    form_columns = ['key', 'value']
    can_delete = False
    can_create = False
    def after_model_change(self, form, model, is_created):
        if model.key == 'admin_password' and not is_created:
            flash('Password changed successfully. Please log in again.', 'info')


class AdminIndexView(AdminIndexView):
    """Custom admin index view."""
    @expose('/')
    def index(self):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.')
            return redirect(url_for('.login'))
        return super().index()

    @expose('/login', methods=['GET', 'POST'])
    def login(self):

        if session.get('admin_logged_in'):
            return redirect(url_for('.index'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            admin_password = Settings.query.filter_by(key='admin_password').first()

            if username == 'admin' and admin_password and password == admin_password.value:
                session['admin_logged_in'] = True
                flash('Logged in successfully')
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('.index'))
            flash('Invalid username or password')

        return self.render('admin/login.html')

    @expose('/logout/')
    def logout(self):
        session.pop('admin_logged_in', None)
        flash('Logged out successfully')
        return redirect(url_for('.login'))