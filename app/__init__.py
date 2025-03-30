"""Application factory module."""
from flask import Flask, url_for, redirect
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy



# Initialize extensions
db = SQLAlchemy()
from app.views.admin_views import AdminIndexView
admin = Admin(name='Subscription Manager', theme= Bootstrap4Theme(swatch = 'minty', fluid=True),index_view=AdminIndexView())


def create_app(config_class='app.config.DevelopmentConfig'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    @app.route('/')
    def index():
        return redirect(url_for('admin.index'))
    # Initialize extensions with app
    db.init_app(app)
    admin.init_app(app)

    with app.app_context():
        # Import models
        from app.models.models import Subscription, OriginalSubscription, Settings, RedirectMapping, User

        # Import views
        from app.views.admin_views import SubscriptionView, OriginalSubscriptionView, SettingsAdmin
        #db.drop_all()
        db.create_all()
        # Register admin views
        admin.add_view(OriginalSubscriptionView(OriginalSubscription, db.session, name='Original Subscriptions'))
        admin.add_view(SubscriptionView(Subscription, db.session, name='Generate Complex Subscriptions'))
        admin.add_view(SettingsAdmin(Settings, db.session, name='Settings'))
        admin.add_link(MenuLink(name='Log out', url='/admin/logout'))

        # Register blueprints
        from app.routes.redirects import redirect_bp
        app.register_blueprint(redirect_bp)
        default_settings = [
            {'key': 'subconverter_api', 'value': 'https://example.com/sub',
             'description': 'example: http(s)://example.com/sub , must end with /sub'},
            {'key': 'base_url', 'value': 'https://localhost:5000',
             'description': 'Please use HTTPS, example: https://example.com(:port), otherwise the copy link will not work'},
            {'key': 'admin_password', 'value': 'admin',
             'description': 'Admin password for the admin panel, default is "admin"'},
        ]
        for setting in default_settings:
            if not Settings.query.filter_by(key=setting['key']).first():
                db.session.add(Settings(**setting))

        db.session.commit()
        # Create database tables

    return app