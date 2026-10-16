import os
import logging
from flask import Flask
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from .config import config

# Initialize SQLAlchemy instance (not bound to any app yet)
db = SQLAlchemy()


def create_app(config_name='default'):
    """Application factory function."""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    Session(app)

    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Import and register blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.student import student_bp
    from .blueprints.professor import professor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(professor_bp, url_prefix='/professor')

    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    app.config['UPLOADS_DIR'] = uploads_dir

    # Route to serve uploaded course materials
    @app.route('/uploads/<path:filename>')
    def serve_material(filename):
        """Serve uploaded course materials."""
        from flask import send_from_directory
        from flask import session

        # Check if user is logged in
        if "user_id" not in session:
            return {"error": "Authentication required"}, 401

        # Get uploads directory
        uploads_dir = app.config.get('UPLOADS_DIR')
        if not uploads_dir:
            return {"error": "Uploads directory not configured"}, 500

        # For now, allow access to any authenticated user
        # In a more advanced system, we would check if the user is enrolled in the course
        # or is the professor who uploaded the material
        try:
            return send_from_directory(uploads_dir, filename)
        except FileNotFoundError:
            # If not found in the main directory, check if it's in a subdirectory
            # This handles paths like "assignments/1/filename.pdf" or "submissions/1/2/filename.pdf"
            try:
                return send_from_directory(uploads_dir, filename)
            except FileNotFoundError:
                return {"error": "File not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500

    # Add security headers for hardening
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Prevent content security policy issues in development
        if app.config.get('ENV') != 'development':
            # In production, you might want to add a proper CSP
            # response.headers['Content-Security-Policy'] = "default-src 'self';"
            pass

        return response

    # Handle file too large error
    @app.errorhandler(413)
    def too_large(e):
        from flask import render_template, request, redirect, url_for, flash
        if request.path.startswith('/professor/') or request.path.startswith('/student/'):
            flash("File is too large. Maximum file size is 16MB.", "error")
            # Redirect back to the upload form or dashboard
            return redirect(request.url or url_for('main.index'))
        return render_template("errors/413.html"), 413

    # Configure logging
    if not app.debug and not app.testing:
        # Setup file logging for production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/student_portal.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Student Portal startup')

    return app