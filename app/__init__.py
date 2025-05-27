from flask import Flask
from .config import Config
from .auth_routes import auth_routes
from .user_routes import user_routes
from .official_routes import official_routes
from .common_routes import common_routes
from .admin_routes import admin_routes

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config.from_object(Config)

    # Register the blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(official_routes)
    app.register_blueprint(common_routes)
    app.register_blueprint(admin_routes)

    # Add any other setup like configurations, db, etc.
    
    return app
