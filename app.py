from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import os
import uuid
from urllib.parse import urlencode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscription_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = 30 * 24 * 60 * 60  # 30 days

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    
    # Add relationship references
    original_subscription = db.relationship('OriginalSubscription', backref='mappings')

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

@app.route('/sub/<friendly_url>')
def subscription_redirect(friendly_url):
    composite = CompositeSubscription.query.filter_by(friendly_url=friendly_url).first_or_404()
    
    # Get all original subscription URLs
    original_urls = []
    for mapping in composite.subscription_mappings:
        original_urls.append(mapping.original_subscription.url)
    
    if not original_urls:
        abort(404)
    
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
    
    return render_template('settings.html', settings=settings_dict)

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
    return render_template('composite_subscriptions.html', subscriptions=subs, original_subs_count=original_subs_count)

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