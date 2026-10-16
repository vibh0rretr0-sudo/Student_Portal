from functools import wraps
from flask import session, redirect, url_for, flash
from ..models import User


def login_user(username, password):
    """Authenticates a user and sets the session."""
    # Find user by username
    user = User.query.filter_by(username=username).first()

    # Check if user exists and password is correct
    if user and user.check_password(password):
        # Set session data
        session['user_id'] = user.id
        session['full_name'] = user.full_name
        session['role'] = user.role
        return {
            'id': user.id,
            'full_name': user.full_name,
            'role': user.role
        }, None

    return None, "Invalid username or password"


def logout_user():
    """Clears the user session."""
    session.clear()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "student":
            flash("Access denied: Students only.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "professor":
            flash("Access denied: Professors only.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Helper to get current user info from session."""
    return {
        "user_id": session.get("user_id"),
        "full_name": session.get("full_name"),
        "role": session.get("role")
    }


def get_current_student():
    """Helper to get student details from session."""
    return get_current_user()


def get_current_professor():
    """Helper to get professor details from session."""
    return get_current_user()