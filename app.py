from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import os
import uuid
from urllib.parse import urlencode, urlparse
import secrets
import base64
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict

app = Flask(__name__)
# Use environment variable or generate a secure random key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///subscription_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = 30 * 24 * 60 * 60  # 30 days

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/subscription_manager.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Subscription Manager startup')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    original_subscriptions = db.relationship('OriginalSubscription', backref='user', lazy=True, cascade='all, delete-orphan')
    composite_subscriptions = db.relationship('CompositeSubscription', backref='user', lazy=True, cascade='all, delete-orphan')

class OriginalSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    mappings = db.relationship('SubscriptionMapping', backref='original_subscription', lazy=True, cascade='all, delete-orphan')

class CompositeSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    friendly_url = db.Column(db.String(100), unique=True, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)  # clash, v2ray, surge, etc.
    config_template = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription_mappings = db.relationship('SubscriptionMapping', backref='composite', lazy=True, cascade='all, delete-orphan')

class SubscriptionMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    composite_id = db.Column(db.Integer, db.ForeignKey('composite_subscription.id'), nullable=False)
    original_id = db.Column(db.Integer, db.ForeignKey('original_subscription.id'), nullable=False)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '').strip()
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email if email else None,
            password_hash=generate_password_hash(password)
        )
        
        # Determine user type logic
        is_first_user = User.query.count() == 0
        
        if is_first_user:
            # First user automatically becomes admin
            user.is_admin = True
            flash('Welcome! You are the first user and have automatically been granted administrator privileges', 'success')
        else:
            # Regular user registration
            user.is_admin = False
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember_me)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
    composite_subs = CompositeSubscription.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', original_subs=original_subs, composite_subs=composite_subs)

@app.route('/privacy-policy')
def privacy_policy():
    """System permissions and data protection information page"""
    return render_template('privacy_policy.html')

@app.route('/user-settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        # Check if username is used by other users
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username is already used by another user', 'error')
            return render_template('user_settings.html')
        
        # Check if email is used by other users
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email and existing_email.id != current_user.id:
                flash('Email is already used by another user', 'error')
                return render_template('user_settings.html')
        
        # If changing password, verify current password
        if new_password:
            if not current_password:
                flash('Current password is required when changing password', 'error')
                return render_template('user_settings.html')
            
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect', 'error')
                return render_template('user_settings.html')
        
        # Update user information
        current_user.username = username
        current_user.email = email if email else None
        
        if new_password:
            current_user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash('User settings updated successfully!', 'success')
        return redirect(url_for('user_settings'))
    
    return render_template('user_settings.html')

@app.route('/original-subscriptions')
@login_required
def original_subscriptions():
    # Can only view own subscriptions
    subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
    return render_template('original_subscriptions.html', subscriptions=subs)

@app.route('/add-original-subscription', methods=['GET', 'POST'])
@login_required
def add_original_subscription():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        url = request.form['url']
        
        # Validate subscription URL
        valid, message = validate_subscription_url(url)
        if not valid:
            flash(message, 'error')
            return render_template('add_original_subscription.html')
        
        subscription = OriginalSubscription(
            name=name,
            description=description,
            url=url,
            user_id=current_user.id
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        flash('Original subscription added successfully!', 'success')
        return redirect(url_for('original_subscriptions'))
    
    return render_template('add_original_subscription.html')

@app.route('/edit-original-subscription/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_original_subscription(id):
    subscription = OriginalSubscription.query.get_or_404(id)
    
    # Check permissions - can only edit own subscriptions
    if subscription.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        subscription.name = request.form['name']
        subscription.description = request.form['description']
        subscription.url = request.form['url']
        
        # Validate subscription URL
        valid, message = validate_subscription_url(subscription.url)
        if not valid:
            flash(message, 'error')
            return render_template('edit_original_subscription.html', subscription=subscription)
        
        db.session.commit()
        flash('Subscription updated successfully!', 'success')
        return redirect(url_for('original_subscriptions'))
    
    return render_template('edit_original_subscription.html', subscription=subscription)

@app.route('/delete-original-subscription/<int:id>', methods=['POST'])
@login_required
def delete_original_subscription(id):
    subscription = OriginalSubscription.query.get_or_404(id)
    
    # Check permissions - can only delete own subscriptions
    if subscription.user_id != current_user.id:
        abort(403)
    
    force_delete = request.form.get('force_delete') == 'true'
    
    # Check if this subscription is used in any composite subscriptions
    mappings = SubscriptionMapping.query.filter_by(original_id=id).all()
    if mappings:
        # Check which composite subscriptions would become empty (have only this subscription)
        composites_that_will_be_empty = []
        composites_that_will_remain = []
        
        for mapping in mappings:
            composite = CompositeSubscription.query.get(mapping.composite_id)
            if composite:
                # Count total mappings for this composite
                total_mappings = SubscriptionMapping.query.filter_by(composite_id=mapping.composite_id).count()
                
                if total_mappings == 1:
                    # This composite only has this one subscription
                    composites_that_will_be_empty.append(composite.name)
                else:
                    # This composite has other subscriptions too
                    composites_that_will_remain.append(composite.name)
        
        # If any composite would become empty, block the deletion unless force delete is used
        if composites_that_will_be_empty and not force_delete:
            error_msg = f'Cannot delete this subscription because it is the ONLY subscription in the following composite subscription(s): {", ".join(composites_that_will_be_empty)}. '
            
            if composites_that_will_remain:
                error_msg += f'It is also used by (but not the only one): {", ".join(composites_that_will_remain)}. '
            
            error_msg += 'Please delete the composite subscriptions first, then delete this original subscription.'
            
            flash(error_msg, 'error')
            return redirect(url_for('original_subscriptions'))
        
        # If force delete is requested, delete empty composite subscriptions
        if force_delete:
            # Delete composite subscriptions that would become empty
            for mapping in mappings:
                composite = CompositeSubscription.query.get(mapping.composite_id)
                if composite:
                    total_mappings = SubscriptionMapping.query.filter_by(composite_id=mapping.composite_id).count()
                    if total_mappings == 1:
                        # This composite will become empty, delete it
                        db.session.delete(composite)
            
            if composites_that_will_be_empty:
                flash(f'Deleted {len(composites_that_will_be_empty)} composite subscription(s) that would become empty: {", ".join(composites_that_will_be_empty)}.', 'info')
            
            if composites_that_will_remain:
                # Remove mappings from composites that will remain
                for mapping in mappings:
                    composite = CompositeSubscription.query.get(mapping.composite_id)
                    if composite and composite.name in composites_that_will_remain:
                        db.session.delete(mapping)
                flash(f'Removed this subscription from {len(composites_that_will_remain)} composite subscription(s) that have other subscriptions.', 'info')
    
    # Delete the original subscription
    db.session.delete(subscription)
    db.session.commit()
    
    flash('Subscription deleted successfully!', 'success')
    return redirect(url_for('original_subscriptions'))

# This route has been redefined above, remove duplicate

@app.route('/add-composite-subscription', methods=['GET', 'POST'])
@login_required
def add_composite_subscription():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        target_type = request.form['target_type']
        config_template = request.form.get('config_template', '')
        custom_url = request.form.get('custom_url', '').strip()
        selected_subs = request.form.getlist('selected_subscriptions')
        
        # Generate friendly URL
        if custom_url:
            # Validate custom URL format
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_url):
                flash('Custom URL can only contain letters, numbers, underscores and hyphens', 'error')
                original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
                return render_template('add_composite_subscription.html', original_subs=original_subs)
            
            # Check if URL is already in use
            if CompositeSubscription.query.filter_by(friendly_url=custom_url).first():
                flash('This custom URL is already in use, please choose another name', 'error')
                original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
                return render_template('add_composite_subscription.html', original_subs=original_subs)
            
            friendly_url = custom_url
        else:
            # Use randomly generated URL
            friendly_url = str(uuid.uuid4())[:8]
            while CompositeSubscription.query.filter_by(friendly_url=friendly_url).first():
                friendly_url = str(uuid.uuid4())[:8]
        
        composite = CompositeSubscription(
            name=name,
            description=description,
            friendly_url=friendly_url,
            target_type=target_type,
            config_template=config_template,
            user_id=current_user.id
        )
        
        db.session.add(composite)
        db.session.flush()  # Get ID
        
        # Add subscription mappings
        for sub_id in selected_subs:
            mapping = SubscriptionMapping(
                composite_id=composite.id,
                original_id=int(sub_id)
            )
            db.session.add(mapping)
        
        db.session.commit()
        
        flash('Composite subscription created successfully!', 'success')
        return redirect(url_for('composite_subscriptions'))
    
    original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
    return render_template('add_composite_subscription.html', original_subs=original_subs)

@app.route('/edit-composite-subscription/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_composite_subscription(id):
    composite = CompositeSubscription.query.get_or_404(id)
    
    # Check permissions - can only edit own subscriptions
    if composite.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        composite.name = request.form['name']
        composite.description = request.form['description']
        composite.target_type = request.form['target_type']
        composite.config_template = request.form.get('config_template', '')
        custom_url = request.form.get('custom_url', '').strip()
        selected_subs = request.form.getlist('selected_subscriptions')
        
        # Handle custom URL update
        if custom_url and custom_url != composite.friendly_url:
            # Validate custom URL format
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', custom_url):
                flash('Custom URL can only contain letters, numbers, underscores and hyphens', 'error')
                original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
                selected_sub_ids = [mapping.original_id for mapping in composite.subscription_mappings]
                return render_template('edit_composite_subscription.html', 
                                     composite=composite, 
                                     original_subs=original_subs,
                                     selected_sub_ids=selected_sub_ids)
            
            # Check if URL is already in use
            existing = CompositeSubscription.query.filter_by(friendly_url=custom_url).first()
            if existing and existing.id != composite.id:
                flash('This custom URL is already in use, please choose another name', 'error')
                original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
                selected_sub_ids = [mapping.original_id for mapping in composite.subscription_mappings]
                return render_template('edit_composite_subscription.html', 
                                     composite=composite, 
                                     original_subs=original_subs,
                                     selected_sub_ids=selected_sub_ids)
            
            composite.friendly_url = custom_url
        
        # Delete old mappings
        SubscriptionMapping.query.filter_by(composite_id=composite.id).delete()
        
        # Add new mappings
        for sub_id in selected_subs:
            mapping = SubscriptionMapping(
                composite_id=composite.id,
                original_id=int(sub_id)
            )
            db.session.add(mapping)
        
        db.session.commit()
        flash('Composite subscription updated successfully!', 'success')
        return redirect(url_for('composite_subscriptions'))
    
    original_subs = OriginalSubscription.query.filter_by(user_id=current_user.id).all()
    selected_sub_ids = [mapping.original_id for mapping in composite.subscription_mappings]
    
    return render_template('edit_composite_subscription.html', 
                         composite=composite, 
                         original_subs=original_subs,
                         selected_sub_ids=selected_sub_ids)

@app.route('/delete-composite-subscription/<int:id>', methods=['POST'])
@login_required
def delete_composite_subscription(id):
    composite = CompositeSubscription.query.get_or_404(id)
    
    # Check permissions - can only delete own subscriptions
    if composite.user_id != current_user.id:
        abort(403)
    
    db.session.delete(composite)
    db.session.commit()
    
    flash('Composite subscription deleted successfully!', 'success')
    return redirect(url_for('composite_subscriptions'))

@app.route('/cleanup-empty-composites', methods=['POST'])
@login_required
def cleanup_empty_composites():
    """Clean up all empty composite subscriptions for current user"""
    empty_composites = []
    
    # Find all composite subscriptions for current user
    user_composites = CompositeSubscription.query.filter_by(user_id=current_user.id).all()
    
    for composite in user_composites:
        if len(composite.subscription_mappings) == 0:
            empty_composites.append(composite.name)
            db.session.delete(composite)
    
    if empty_composites:
        db.session.commit()
        flash(f'Cleaned up {len(empty_composites)} empty composite subscription(s): {", ".join(empty_composites)}', 'success')
    else:
        flash('No empty composite subscriptions found', 'info')
    
    return redirect(url_for('composite_subscriptions'))

@app.route('/sub/<friendly_url>')
def subscription_redirect(friendly_url):
    composite = CompositeSubscription.query.filter_by(friendly_url=friendly_url).first_or_404()
    
    # Get all original subscription URLs
    original_urls = []
    for mapping in composite.subscription_mappings:
        original_urls.append(mapping.original_subscription.url)
    
    if not original_urls:
        # Return a custom error page for empty composite subscriptions
        return render_template('error.html', 
                             error_title='Empty Composite Subscription',
                             error_message=f'The composite subscription "{composite.name}" contains no original subscriptions. Please add some original subscriptions to this composite subscription or delete it.',
                             back_url=url_for('composite_subscriptions')), 404
    
    # Get system settings
    subconverter_url = get_setting('subconverter_url', 'https://api.subconverter.com/sub')
    
    # Build conversion URL
    params = {
        'target': composite.target_type,
        'url': '|'.join(original_urls)
    }
    
    if composite.config_template:
        params['config'] = composite.config_template
    
    redirect_url = f"{subconverter_url}?{urlencode(params)}"
    
    return redirect(redirect_url)

@app.route('/settings')
@login_required
def settings():
    if not current_user.is_admin:
        abort(403)
    
    settings_list = SystemSettings.query.all()
    settings_dict = {s.key: s.value for s in settings_list}
    
    # Get system information
    import sys
    import flask
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    flask_version = flask.__version__
    
    return render_template('settings.html', 
                         settings=settings_dict,
                         python_version=python_version,
                         flask_version=flask_version)

@app.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    if not current_user.is_admin:
        abort(403)
    
    subconverter_url = request.form['subconverter_url']
    base_url = request.form['base_url']
    
    update_setting('subconverter_url', subconverter_url, 'Subconverter API Address')
    update_setting('base_url', base_url, 'Application Base URL')
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    
    # Only calculate basic statistics, don't expose specific subscription information
    admin_count = sum(1 for user in users if user.is_admin)
    
    return render_template('admin_users.html', 
                         users=users,
                         admin_count=admin_count)

@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    if not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '').strip()
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('admin_create_user.html')
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('admin_create_user.html')
        
        # Create new user
        user = User(
            username=username,
            email=email if email else None,
            password_hash=generate_password_hash(password),
            is_admin=is_admin
        )
        
        db.session.add(user)
        db.session.commit()
        
        user_type = "Administrator" if is_admin else "Regular User"
        flash(f'{user_type} "{username}" created successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_create_user.html')

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Don't allow modifying own admin status
        if user.id == current_user.id:
            flash('Cannot modify your own account permissions', 'error')
            return render_template('admin_edit_user.html', user=user)
        
        username = request.form['username']
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        
        # Check if username and email are used by other users
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username is already used by another user', 'error')
            return render_template('admin_edit_user.html', user=user)
        
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email and existing_email.id != user.id:
                flash('Email is already used by another user', 'error')
                return render_template('admin_edit_user.html', user=user)
        
        # Update user information
        user.username = username
        user.email = email if email else None
        user.is_admin = is_admin
        
        # If new password is provided, update password
        if password:
            user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        
        flash(f'User "{username}" information updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    # Don't allow deleting the last admin
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('Cannot delete the last administrator account', 'error')
            return redirect(url_for('admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" has been deleted', 'success')
    return redirect(url_for('admin_users'))

def get_setting(key, default=None):
    setting = SystemSettings.query.filter_by(key=key).first()
    return setting.value if setting else default

def update_setting(key, value, description=None):
    setting = SystemSettings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = SystemSettings(key=key, value=value, description=description)
        db.session.add(setting)
    db.session.commit()

# Add missing functions
def get_original_subscription(id):
    return OriginalSubscription.query.get_or_404(id)

# Fix composite subscription route issues
@app.route('/composite-subscriptions')
@login_required
def composite_subscriptions():
    # Can only view own subscriptions
    subs = CompositeSubscription.query.filter_by(user_id=current_user.id).all()
    original_subs_count = OriginalSubscription.query.filter_by(user_id=current_user.id).count()
    
    # Check for empty composite subscriptions
    empty_subs = []
    for sub in subs:
        if len(sub.subscription_mappings) == 0:
            empty_subs.append(sub)
    
    return render_template('composite_subscriptions.html', 
                         subscriptions=subs, 
                         original_subs_count=original_subs_count,
                         empty_subs=empty_subs)

@app.route('/check-deletion/<int:id>')
@login_required
def check_deletion(id):
    """Check if deletion of original subscription would be blocked"""
    subscription = OriginalSubscription.query.get_or_404(id)
    
    # Check permissions - can only check own subscriptions
    if subscription.user_id != current_user.id:
        abort(403)
    
    # Check if this subscription is used in any composite subscriptions
    mappings = SubscriptionMapping.query.filter_by(original_id=id).all()
    
    result = {
        'can_delete': True,
        'warning_message': '',
        'composites_that_will_be_empty': [],
        'composites_that_will_remain': []
    }
    
    if mappings:
        # Check which composite subscriptions would become empty (have only this subscription)
        composites_that_will_be_empty = []
        composites_that_will_remain = []
        
        for mapping in mappings:
            composite = CompositeSubscription.query.get(mapping.composite_id)
            if composite:
                # Count total mappings for this composite
                total_mappings = SubscriptionMapping.query.filter_by(composite_id=mapping.composite_id).count()
                
                if total_mappings == 1:
                    # This composite only has this one subscription
                    composites_that_will_be_empty.append(composite.name)
                else:
                    # This composite has other subscriptions too
                    composites_that_will_remain.append(composite.name)
        
        # If any composite would become empty, block the deletion
        if composites_that_will_be_empty:
            result['can_delete'] = False
            result['composites_that_will_be_empty'] = composites_that_will_be_empty
            result['composites_that_will_remain'] = composites_that_will_remain
            
            warning_msg = f'Cannot delete this subscription because it is the ONLY subscription in the following composite subscription(s): {", ".join(composites_that_will_be_empty)}. '
            
            if composites_that_will_remain:
                warning_msg += f'It is also used by (but not the only one): {", ".join(composites_that_will_remain)}. '
            
            warning_msg += 'Please delete the composite subscriptions first, then delete this original subscription.'
            result['warning_message'] = warning_msg
    
    return jsonify(result)

def validate_subscription_url(url):
    """
    Validate subscription URL by checking if it's accessible and contains valid content
    """
    try:
        # Parse URL to check format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"
        
        # Try to fetch the URL with timeout
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            return False, f"URL returned status code {response.status_code}"
        
        content = response.text.strip()
        
        # Check if content looks like a subscription (base64 encoded or contains proxy configs)
        if not content:
            return False, "URL returned empty content"
        
        # Try to decode as base64 (common for subscription links)
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            if any(keyword in decoded.lower() for keyword in ['vmess://', 'vless://', 'ss://', 'ssr://', 'trojan://', 'hysteria://']):
                return True, "Valid subscription content detected"
        except:
            pass
        
        # Check for direct proxy protocol URLs
        if any(protocol in content.lower() for protocol in ['vmess://', 'vless://', 'ss://', 'ssr://', 'trojan://', 'hysteria://']):
            return True, "Valid proxy configuration detected"
        
        # Check for YAML/JSON config files (Clash format)
        if any(keyword in content.lower() for keyword in ['proxies:', 'proxy-groups:', 'rules:']):
            return True, "Valid Clash configuration detected"
        
        return False, "Content doesn't appear to be a valid subscription"
        
    except requests.exceptions.Timeout:
        return False, "Request timeout - URL may be slow or unreachable"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - URL may be unreachable"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

@app.route('/test-subscription/<int:id>')
@login_required
def test_subscription(id):
    """Test if a subscription URL is working"""
    subscription = OriginalSubscription.query.get_or_404(id)
    
    # Check permissions
    if subscription.user_id != current_user.id:
        abort(403)
    
    valid, message = validate_subscription_url(subscription.url)
    
    return jsonify({
        'valid': valid,
        'message': message,
        'subscription_name': subscription.name
    })

@app.route('/test-composite/<int:id>')
@login_required  
def test_composite(id):
    """Test if a composite subscription is working"""
    composite = CompositeSubscription.query.get_or_404(id)
    
    # Check permissions
    if composite.user_id != current_user.id:
        abort(403)
    
    if not composite.subscription_mappings:
        return jsonify({
            'valid': False,
            'message': 'Composite subscription is empty',
            'subscription_name': composite.name
        })
    
    # Test the generated URL
    try:
        # Get all original subscription URLs
        original_urls = []
        for mapping in composite.subscription_mappings:
            original_urls.append(mapping.original_subscription.url)
        
        # Get system settings
        subconverter_url = get_setting('subconverter_url', 'https://api.subconverter.com/sub')
        
        # Build conversion URL
        params = {
            'target': composite.target_type,
            'url': '|'.join(original_urls)
        }
        
        if composite.config_template:
            params['config'] = composite.config_template
        
        test_url = f"{subconverter_url}?{urlencode(params)}"
        
        # Test the conversion
        response = requests.get(test_url, timeout=15)
        
        if response.status_code == 200:
            return jsonify({
                'valid': True,
                'message': 'Composite subscription is working correctly',
                'subscription_name': composite.name
            })
        else:
            return jsonify({
                'valid': False,
                'message': f'Conversion service returned status {response.status_code}',
                'subscription_name': composite.name
            })
            
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Test failed: {str(e)}',
            'subscription_name': composite.name
        })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_title='Page Not Found',
                         error_message='The page you are looking for does not exist.',
                         back_url=request.referrer or url_for('dashboard')), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html',
                         error_title='Access Forbidden', 
                         error_message='You do not have permission to access this resource.',
                         back_url=request.referrer or url_for('dashboard')), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('error.html',
                         error_title='Internal Server Error',
                         error_message='An unexpected error occurred. Please try again later.',
                         back_url=url_for('dashboard')), 500

@app.route('/api/stats')
@login_required
def api_stats():
    """Get subscription statistics for current user"""
    user_id = current_user.id
    
    # Basic counts
    original_count = OriginalSubscription.query.filter_by(user_id=user_id).count()
    composite_count = CompositeSubscription.query.filter_by(user_id=user_id).count()
    
    # Get creation dates for charts
    original_subs = OriginalSubscription.query.filter_by(user_id=user_id).all()
    composite_subs = CompositeSubscription.query.filter_by(user_id=user_id).all()
    
    # Group by month for trend analysis
    monthly_stats = defaultdict(lambda: {'original': 0, 'composite': 0})
    
    for sub in original_subs:
        month_key = sub.created_at.strftime('%Y-%m')
        monthly_stats[month_key]['original'] += 1
    
    for sub in composite_subs:
        month_key = sub.created_at.strftime('%Y-%m')
        monthly_stats[month_key]['composite'] += 1
    
    # Target type distribution
    target_types = {}
    for sub in composite_subs:
        target_types[sub.target_type] = target_types.get(sub.target_type, 0) + 1
    
    return jsonify({
        'totals': {
            'original': original_count,
            'composite': composite_count,
            'total': original_count + composite_count
        },
        'monthly_trends': dict(monthly_stats),
        'target_types': target_types,
        'recent_activity': {
            'last_original': original_subs[-1].created_at.isoformat() if original_subs else None,
            'last_composite': composite_subs[-1].created_at.isoformat() if composite_subs else None
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize default settings
        if not SystemSettings.query.filter_by(key='subconverter_url').first():
            update_setting('subconverter_url', 'https://api.subconverter.com/sub', 'Subconverter API Address')
        
        if not SystemSettings.query.filter_by(key='base_url').first():
            update_setting('base_url', 'http://localhost:5000', 'Application Base URL')
    
    # Listen on all interfaces for Docker deployment
    app.run(host='0.0.0.0', port=5000, debug=False) 