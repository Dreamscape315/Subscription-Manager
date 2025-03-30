"""Database models for the application."""
from app import db

class OriginalSubscription(db.Model):
    """Model for original subscription sources."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<OriginalSubscription {self.name}>"


class Subscription(db.Model):
    """Model for generated subscriptions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<Subscription {self.name}>"


class RedirectMapping(db.Model):
    """Model for redirect mappings to actual subscription URLs."""
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(10), unique=True, nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    subscription_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<RedirectMapping {self.unique_id}>"


class Settings(db.Model):
    """Model for application settings."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Settings {self.key}>"


class User(db.Model):
    """Model for user authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)