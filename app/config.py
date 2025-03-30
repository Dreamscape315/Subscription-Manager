"""Application configuration."""
import secrets
secrets_key = secrets.token_hex(16)  # Generate a random secret key

class Config:
    """Base configuration."""
    SECRET_KEY = secrets_key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///subscriptions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False