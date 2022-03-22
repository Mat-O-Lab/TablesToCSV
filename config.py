import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a6adf2ad7d50c0f8c2a02fbae47b05636588e2edcf9298af092f7c0a724d7ed1"
    TEMPORAL_FOLDER = os.environ.get("TEMPORAL_FOLDER") or "tmp"
    TEMPLATES_AUTORELOAD = True

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}