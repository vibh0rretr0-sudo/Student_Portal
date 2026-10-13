from flask import session, redirect, url_for, request, jsonify
from functools import wraps
from database import get_user_by_username, get_student_by_user_id, get_professor_by_user_id, _verify_password


def login_user(username, password):
    user = get_user_by_username(username)
    if not user:
        return None, "Invalid username or password"
    if not _verify_password(password, user['password_hash']):
        return None, "Invalid username or password"
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']
    return user, None


def logout_user():
    session.clear()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        if session.get('role') != 'student':
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Student access required'}), 403
            return redirect(url_for('professor_dashboard'))
        return f(*args, **kwargs)
    return decorated


def professor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        if session.get('role') != 'professor':
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Professor access required'}), 403
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated


def get_current_student():
    if 'user_id' not in session or session.get('role') != 'student':
        return None
    return get_student_by_user_id(session['user_id'])


def get_current_professor():
    if 'user_id' not in session or session.get('role') != 'professor':
        return None
    return get_professor_by_user_id(session['user_id'])
