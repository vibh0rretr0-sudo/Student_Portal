import os
from flask import Flask
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # CSRF Protection
    csrf = CSRFProtect(app)

    # Global Error Handling
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Session configuration
    Session(app)

    # Import and register blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.student import student_bp
    from .blueprints.professor import professor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(professor_bp, url_prefix='/professor')

    return app
